from __future__ import annotations

import base64
from dataclasses import dataclass, field, replace
import hashlib
import itertools
import math
import re
import struct
from types import MappingProxyType
from typing import Any, Mapping
import xml.etree.ElementTree as ET
import zlib

from interchange import (
    BooleanOperation,
    CadDocument,
    Capability,
    CircleGeometry,
    ExtrusionEndCondition,
    ExtrusionFeature,
    FeatureKind,
    FeatureStep,
    FilletFeature,
    LineGeometry,
    Parameter,
    ParameterRole,
    Sketch,
    SupportPlane,
    ValueKind,
)

from .container import SldprtFormatError
from .format import (
    CANONICAL_PLANE_FEATURE_TYPE,
    CLASS_MARKER,
    DIMENSION_SCALAR_HEADERS,
    PART_SUFFIX,
    PLANE_FEATURE_TYPES,
    dimension_scalar_value_offset,
)

_CURRENT_MARKER = bytes.fromhex("ffff1f0003")
_LEGACY_MARKER = bytes.fromhex("ffff070001")
_EXTENDED_MARKER = bytes.fromhex("ffff1f0001")
_MARKERS = (_CURRENT_MARKER, _LEGACY_MARKER, _EXTENDED_MARKER)
_COORDINATE_TAG = bytes.fromhex("1e00")
_POINT_LOCUS = bytes.fromhex("04000200")
_CIRCLE_LOCUS = bytes.fromhex("05000100")
_NUMBER = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")
_EDGE_SELECTION_IDENTITY = bytes.fromhex("7dc39425ad49b2547dc39425ad49b254")
MARKER_LOCAL_ID_OFFSET_BY_LENGTH = MappingProxyType(
    {
        142: 138,
        146: 138,
        152: 148,
        154: 150,
        156: 148,
        158: 144,
        162: 158,
        166: 158,
        167: 158,
    }
)


@dataclass(frozen=True, slots=True)
class NativeOperand:
    offset: int
    kind_code: int
    entity_index: int


@dataclass(frozen=True, slots=True)
class NativeScalar:
    name: str
    name_offset: int
    value_offset: int
    value: float
    object_id: int | None
    role: str
    operands: tuple[NativeOperand, ...]


@dataclass(frozen=True, slots=True)
class NativeDimension:
    name: str
    value_mm: float
    kind: str
    source_text: str
    native_value: float | None = None
    native_offset: int | None = None
    native_role: str | None = None
    operands: tuple[NativeOperand, ...] = ()


@dataclass(frozen=True, slots=True)
class NativeName:
    offset: int
    text_end: int
    name: str
    object_id: int | None
    class_token: int


@dataclass(frozen=True, slots=True)
class NativeClass:
    offset: int
    name: str


@dataclass(frozen=True, slots=True)
class NativeMarker:
    offset: int
    length: int
    prefix: str
    native_kind: int
    locus: str
    profile_role: int
    state: float | None
    object_index: int | None
    local_id: int | None
    coordinates_mm: tuple[float, float] | None
    endpoint_indices: tuple[int, int] | None
    construction: bool
    semantic: str
    data: bytes = b""


@dataclass(frozen=True, slots=True)
class NativeConstraint:
    id: str
    kind: str
    references: tuple[str, ...]
    parameter: str | None
    value: float | None
    native_offset: int | None
    native_code: int | None


@dataclass(frozen=True, slots=True)
class NativeProfile:
    kind: str
    coordinates: tuple[float, ...]
    marker_offsets: tuple[int, ...]
    parameter_name: str | None = None
    dimension_kind: str | None = None


@dataclass(frozen=True, slots=True)
class NativePlane:
    object_id: int
    name: str
    origin_mm: tuple[float, float, float]
    normal: tuple[float, float, float]
    u_axis: tuple[float, float, float]
    v_axis: tuple[float, float, float]
    native_offset: int | None
    native_length: int | None
    principal: bool = False


@dataclass(frozen=True, slots=True)
class NativeSketch:
    object_id: int
    name: str
    support_plane_id: int
    native_offset: int
    native_end: int
    markers: tuple[NativeMarker, ...]
    profiles: tuple[NativeProfile, ...]
    dimensions: tuple[NativeDimension, ...]
    constraints: tuple[NativeConstraint, ...]


@dataclass(frozen=True, slots=True)
class NativeEndSpec:
    offset: int
    termination_code: int
    direction_code: int
    second_direction_code: int


@dataclass(frozen=True, slots=True)
class NativeOperation:
    object_id: int
    name: str
    kind: str
    profile_id: int | None
    dependencies: tuple[int, ...]
    native_offset: int
    native_end: int
    length_mm: float | None
    radius_mm: float | None
    family_code: int | None
    operation_code: int | None
    schema_code: int | None
    direction_code: int | None
    termination_code: int | None
    selection_offsets: tuple[int, ...]
    selected_local_ids: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class NativeFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    native_offset: int | None
    native_end: int | None
    properties: dict[str, str]
    dimensions: tuple[NativeDimension, ...]
    data: bytes = b""


@dataclass(frozen=True, slots=True)
class NativeConfiguration:
    object_id: int
    name: str
    configuration_id: int
    properties: dict[str, str]


@dataclass(frozen=True, slots=True)
class NativeModel:
    configurations: tuple[NativeConfiguration, ...]
    features: tuple[NativeFeature, ...]
    planes: tuple[NativePlane, ...]
    sketches: tuple[NativeSketch, ...]
    operations: tuple[NativeOperation, ...]
    names: tuple[NativeName, ...]
    classes: tuple[NativeClass, ...]
    scalars: tuple[NativeScalar, ...]
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class NativePartStreams:
    keywords: bytes
    features: bytes
    resolved_features: bytes
    configuration_lanes: tuple[tuple[int, bytes], ...]
    native_capabilities: frozenset[Capability]
    object_ids: Mapping[str, int]
    envelope_streams: Mapping[str, bytes]


@dataclass(slots=True)
class _XmlFeature:
    object_id: int
    name: str
    kind: str
    xml_tag: str
    properties: dict[str, str]
    dimensions: list[NativeDimension]


@dataclass(frozen=True, slots=True)
class _WriteDimension:
    name: str
    value_mm: float
    text: str
    role: ParameterRole


@dataclass(frozen=True, slots=True)
class _WriteObject:
    source_id: str
    object_id: int
    name: str
    xml_tag: str
    kind: str
    class_name: str
    properties: tuple[tuple[str, str], ...] = ()
    dimensions: tuple[_WriteDimension, ...] = ()
    payload: bytes = b""


@dataclass(frozen=True, slots=True)
class _NativeIdentity:
    creation_stamp: int
    last_modified_stamp: int
    baseline_stamp: int
    header_stamp: int
    configuration_flags: int
    reference_name: str


_BASE_OBJECTS = (
    (8, "Comments", "Comments", "moCommentsFolder_c"),
    (23, "Favorites", "Favorites", "moFavoriteFolder_c"),
    (24, "History", "History", "moHistoryFolder_c"),
    (25, "Selection Sets", "Selection Sets", "moSelectionSetFolder_c"),
    (22, "Sensors", "Sensors", "moSensorFolder_c"),
    (7, "Design Binder", "Design Binder", "moDocsFolder_c"),
    (1, "Annotations", "Annotations", "moDetailCabinet_c"),
    (17, "Notes", "Notes", "moNotesAreaFtrFolder_c"),
    (18, "Notes1___EndTag___", "Notes", "moNotesAreaFtrFolder_c"),
    (10, "Surface Bodies", "Surface Bodies", "moSurfaceBodyFolder_c"),
    (9, "Solid Bodies", "Solid Bodies", "moSolidBodyFolder_c"),
    (21, "Markups", "Markups", "moInkMarkupFolder_c"),
    (16, "Equations", "Equations", "moEqnFolder_c"),
    (
        11,
        "Material <not specified>",
        "SOLIDWORKS Materials",
        "moMaterialFolder_c",
    ),
    (2, "Front Plane", "Plane", "moRefPlane_c"),
    (3, "Top Plane", "Plane", "moRefPlane_c"),
    (4, "Right Plane", "Plane", "moRefPlane_c"),
    (5, "Origin", "Origin", "moOriginProfileFeature_c"),
)
_KEYWORD_ONLY_OBJECTS = (
    (6, "Lights and Cameras", "Lights and Cameras"),
    (12, "Ambient", "Ambient"),
    (13, "Directional1", "Directional"),
    (14, "Directional2", "Directional"),
    (15, "Directional3", "Directional"),
    (19, "", "Exploded Views"),
)
_KEYWORD_ONLY_OBJECT_IDS = frozenset(item[0] for item in _KEYWORD_ONLY_OBJECTS)
_SYSTEM_OBJECT_IDS = frozenset(range(1, 26))
_NAME_TOKEN = 0x8004
_NAME_PREFIX = struct.pack("<H", _NAME_TOKEN) + b"\xff\xfe\xff"
_SCALAR_HEADER = DIMENSION_SCALAR_HEADERS[0]
_SOLIDWORKS_XML_NAMESPACE = "http://www.solidworks.com/sw2003/schema"
_SOLIDWORKS_CONFIGURATION_FLAGS = -2143288960
_BASE_CONFIGURATION_MANAGER = (
    b"c-qBOJ4*vW5dJm~R1gc%!bU`}wGazQ;RPdt_()LDCJ@fc84oVGuy<+Yz+a)Dg|(%9dON{Zun_FTUyyV59=V4XjVL"
    b"<D?#|Ba&V2LOa~y^#G>wwcI@TH;E?b(>+G+5bf`Ez+kzkyjgE*;)Jt`X^zx*;AToU)Qj!%Hyjo-@mIibIve`G!Wy"
    b"pqAqX&%g#GE5W5ip;GT(3&Dt<D}X(>gulCR7uivM%D@0F=TY0!|KQ3&Y3U{$B+F$Gdr?g;YM5KmZq9D<?jA9ghZ!"
    b"l<oC&vN}uk_-=z5Z<gX7BQiw&?U<k_rp9{TB)MMz|G|MoF)1V;hL9-K1>=dWABn)4i&#e0UZa5GPZ>NL;s;Gd&K!"
    b"au(P0V3~9O?wcB;7vB*v2N-aY)=Awn#FE5}oG+FkN3ooh(^2s=n1WPTU}b#ipxMNv;v6yE29B>8{O1I=e(?M7vM~"
    b"l88p6%a}YXh~d_geU^c={q35!dRgeVfmh&^_WoUp+7Eb^<o&0He|l&l4Ma98+Jc`U8OPrc`(`SKE7zO!Q@w}FzPw"
    b"sU=AWfvXR*gNTx={-752+{&7^u8)M#I1qnlETgr%_iJj(h1xZH>47qO1Q?39nTHPag04P*8&@g@5qis2nm7Z=6"
)
_BASE_CONFIGURATION = (
    b"c-rk8eQ*?4{q0=>A%udIDy<c-RiMoX6F#ObACtX&5Qrw>dbt30Lc`{=T&}s>je8s5sM8*TW2ePxr~V;Kt;nb|Ivo"
    b"d8Y#o_iXc^I3n4&nM0~XO1T5Ox@40N<|{@&a7cK3GoK0@x2qujgMdvD*z@BO~sd%w4D_m@g>s0u}8pP;Bc!6&K_3"
    b"BDGDQczL@B^`2~*dav4o?z-~s?vu9q#zY7LNs{spJxZuznUT$xZNyhw=NtT5+XiD9uyTdEXI0*ubh0BwIa1KyiR~"
    b"6!Y@MeNBH#k9F0%$$RTj1m|Yk$OIH}Z-P8xYYzFLypf42-!oPrGkP4$9a%-q1ES)4AI!*8x@ZLSQ*3<i>aUnB#?M"
    b"-Mo>P9|bmyAO2FQ6#$pcd#b0;t5GtP`z8ZKxGBqxF#Tqc1>?2Q@)`1rT&D??!z9NrkJMLLEf?ga`~VO3FmY4?`+K"
    b"@`3;_LSQb0x{IMsDwV<%@R%CRE_vq8<@h4<<g#(V>Hg=9TC8zFR|8GJx>^(~nBlWDXH8>*&22zMZvqwVlEP{%AoN"
    b"B+xo42vn<2MNltOBMS4>n$c~8(q!R+0G!!P*?dVkk~=D>gNc#E&HXrUHby)0FoaHW-u@SFvL%Mk(#Zi@0uK(0XwM"
    b"MMYO9-j4+)qmT*i?6mo=CVRYI?)|N(Ov*rD8Lx(3;^3KO0lpSF9=LG&U5SFX9M__h%Bf@K>ZT{yK_(pOQ9xNim8I"
    b"67L+R(SZ6#|5SSIZHn+%1P%H>c7lAn)GeK3vSgfGLuU3RDg;EK&*0hBsQBc}tRaOcL*DtGr5-%)VEGnP8wV)#yi)"
    b"xi5Dxr7*fldRUfpAnTAjpqnHC4nf4T(}PUeFQyF*>Z8<mjL*iIS=TO|NtdrbrQ_m|xuNiwKg~ET}?HkU{O-bp=&^"
    b"CWLzOT6nzQ@Gjq7cmB!vs(P)bA4B*R1eAdRV+*2AMKuZqH}nf?u%DP@vl~zc*afX<2^eJ_bQh$s#UVkuk=Ox2G=Q"
    b"*~h4Vyow*~G9Z#Je<G_by~0oX36q7oJ&&>I~VbXEtO5$r-J><JoN(OVnqGH{A2)R5c`)?`Fudv2Of1z4&N8HVYM`"
    b"6M|*;{^;-G14BQIGC*gW92v2{|Z`1Q?x!%EN=zE;`{JN@BhBNcN1iAn($n7;l(Z9@BjN_hd%g6{qsHbUtHAvPQ7-"
    b"2wBB6jyE}Tq51gCFk4(G#WyM{`Yxk3g>T1BfeDinw`&(Y$!8@6)Hr000b4;=pG?1D(W;VI9DIS;Ms@B?aQT*?UA}"
    b"tQmc!0)3G(JRQNsGA{xm$y_lNj$0IP}p8m6)oj&BS02lHoK+_6&G1LCLf=kPd+X?jeSLn3&mNs1e7dHEnRe)w!$+"
    b"oB2_)4-tvUj`REwN1={{`iK#a_bpA3lAy*A+{XddYG|iYlRy5}yhT;dMQqy?O*?$Nb%<Ms{x>;Id4IY?JsAFhk3Z"
    b"tyIQ+Ys0se>8Epvxl+j$0u#oDk@c{WdL^&aA%cxmC|b3WLhx6|M+8#YhDvvN#}4Ca3xdFZhE^frDlw%|Vhk=OVGo"
    b"^;zen<iJ-2GR({>2W?=UZ#x-XNlQ>cj;C+t2s<_N54-nLUqDD=6%ALSLt!kIOwCg2{yDHC;*F92kL@!7c5b1JDsb"
    b"Xvze>L<UaAzzgCm`#*<wmS01r9p47_{ztJS_ny}TGD@%UDSLgD0ztN=5=+GqkfX;JQ0X4u~9`_|a?m3fHn<<p%h8"
    b"uBi7%$12ukv1P>~g!MJbKG}H<bR2kDbWcSAS%(`ZXEF`HYA7Db^c(g`ntMv5sTTv|=&+#P^@xfAUjDPwe7ZY<j(b"
    b"+kmoRVCEH9QgkEw%paNPv%=y^o&wI{oTPLyX8N_T#JTFS9Sn}}rHyf}zApH?yDo1O`0VFAxz9*SmjlQ$mP;2~^IA"
    b"|`%tj+!gLf)lx~tV>xTe50m5x#-ZKvlg6*g?go2L_xfzvrUUe!wjGxO__rNb-sRspkLtxs^RcC2fRcI@?~QKccLi"
    b"O0hHRL6zTb)vu4lZc7On7tNcwz)Zn(dIP6o8Ad>nnlKEUpX%8-gru-+(-U>%to1a(N0f^KKk0~Dr;-W_QCc;+M8~"
    b"h^k<SzPp-IYo`1P<w1>uPl`3m=Y4*XP@zVh`A=XHFG?e=ot(KOxwXChzm$sUp1ZBIN0*5~u=mca#fS?G7cA-|*QF"
    b"3e>FYUn9*c=zFD=yP9a9UtHdMj5r=jJYl!&-La_4RiS?Yr{p1NAHh5F80b<)`EMaS1Uv{V32l;>>h(ZGLDm3N6m1"
    b";W<AS=dz5AqH*xL16-b1Mmw>TIW}63u~#Jww&dsU;ab|5U(L|xd^-%SxOfvm$<5iB%1aDUj^i?Ef>rh<gn721|H7"
    b"QFUb_E<XL%Mg2weI>aVnc)mk_B7nr^>z{+?={J<QeaZ{v-0tu4)tFN}1ZE#C@@)=QdS%}hTA@s6^rj(38|@T76l`"
    b"Z{PnePn}=FZR+O<8-z@a=i#`6%ON>1qa><SCoYYE(eW;D(A*<Sz+(oqkSb$V;kSi$7JSvt^QNA-BUI=nRuORYOO@"
    b"Zr}w=tu3RS1+_`LN;(3VO%a<nZC7zSu9%A<j(%`Y5d5u>~GkxpNJP<r{)N?@T-(icjR#o2g*fL>QD9E*SWphbQ5x"
    b"2*M=))=@=yQ^fIPAh7%72bc#@sgg&t4EVxd5x|1bjsDX+5%Yse3MR{-l2{K=;6ZJ8D1yv<mrQ25vxYdVU+^bpX8q"
    b"v_{WsAUU{Xkwe~MQ=SAfdxXsF&Cs6$si3WAb1gsNt6-`FxbMDJ+#8|R5OFOKCVhBF&NhhKh&)3?hPi96hn&8&x(2"
    b"U3(7Q-*jzBs<bz*>c9*My(H}nR=7r|6hB=usp9LyhqKo}yWz?)k~&l~5_&-~x4lD4$Skv{C=q#^+w%xt6n9#rVW1"
    b"Kn$gG!f@+B5}tSV=%mv%my!g`pCQ>HAH*EqNKKkL;Wg+J-Gp3^a6ZsaM3VaV}p_&L~922k;1~#3v+af8!oru-zAZ"
    b">&vM2L)3N>x_xkrQ{?Ub=d!$n5(Gn8=z}vZ%vdwkS=ah7U78p(g(?+}@fjTeaJ$7~099G1j8kQw9lWOcE2kV*+d3"
    b"ajsu#0_}z}Uv(4D6cbOj^Ed+f2gkUKU$htWIQO;9{MDH<b<pQ3gg9hk+XOslyrrXER0)=f}V$Is>PdDg%EzE*f~}"
    b"FlD6o_^UX4=xBJ!X5ul?g<!(|JI`{lW3H736S%Y)y$Z#K*7mlAV=BAHZc4?i#E({WEv(ttMNd>;z2sb``Usy_4Z~"
    b"&|N#?l;Kt8N%lWI{5_2#7(2^TJ3Tq<i}<rT<k&RL1^Yz&<^p`=#Q+k_P(T7KA4o-7JQu2E3bMx4T`h`UM@?7bWq>"
    b"KNH5w6rfQMeb4Pi(fZTIA@%!IN0u!<3dwKzBE<Tl94#5Yn?>~Mo7okCaYvo>8Z?@p2@Yu)>Vl|zNn2Vl!GdpMi!N"
    b"-N%>L*vu7)qzA`a`RqA(;duhd^o1fkHCXcQ>dBN@ZOA>Xxc;;gKJjErka><eI#kbw@Ht$^%pY>VDKdseIUc9W;e="
    b"lIJUtroMkAk)Up(u^E){3WB%y0iEzv<kA&1;XINFMzB^h0%f|4eZiT)F?!mN{=nFYzbN{?D`M;dA`IzjF7wb$>mZ"
    b"{KccM@zdu+ym9iCj>e0{p{*)k+NRW!y=WR`FH@<#a(c!3ef)2dZ@xV5nKQ4x!6-X?;lQ?IUpw_Kf9~FdsLnmf|A|"
    b"WNAgzBgt$u+io08AsiLKcP(yRx(+iDR7wMmZ1N<ipkjwh=v+daJH=o}E$V1Hvo4i4xpCAGbrgImku8+F*8`QEqRx"
    b"X-X>j_>~0Y5Djkz2CZjxuV`P^AN82px&kfrn+NDyEq!>IE$gqV}0#{GT;}3veMTRbUT;@vn;VWbR;a#%c(!sra-?"
    b"U3VnWYb2>9KKZ|BQVttCbYTIB0+h*;8B!tpkjNUvE1~yAO8`uVvOl}U%Nc|s6(rNk"
)
_BASE_LIGHTWEIGHT_DATA = (
    b"c-kvsAOt?_$3fd;rx^}_Nr!%i|Nj{oxERutBQg?8k~89y|Nr|h;mF{}5X|7oV9a31punI3WEC;wGvoo;PC!;BLo!"
    b"1)P`(5#mdc=s?iQFG42(eh9|}NxW(JUL!VJ0jKH&j5iFv7h`6;O`i6x0(Yk6{k1_l8QOk)UO$YDqX8y*j|3@FF#2"
    b"6aLS&=Ck(CM1hU0|-Z=1NW1wi+N6Lv)790KlD{&jXj$9eyI3<n7EShSADh<yX*;>ORPL2iSGXc3|yF-(cB30!+u~"
    b"0ih@Gd1suAG45h#jEI|tEJfKV>P$Ur?-pmaIVuLdTC|7_I6U-#X1fh^X!~~2F^A*gOXyW@xiwRur_^=<DhaA&`Fe"
    b"bQzfY~vfAp<R6un-*^#D)?Apv3}u?Cgj695pr=8gSU#Kuj#a0CKF;KQ^!f09xS=n*"
)
_BASE_DEFINITION = (
    b"c-qZZJ!}(a7=G^@<HXJ{RANKf0z+F`i3yPZqa?%x#ZIaYtz*uYU~;~T&URYL(5NgOkUCUd*Z_%%r9(TE!3=bbGIZ"
    b"%cg~U>oN+76&ghb8rz2BLf|L;IZeAb=)-M!EIKJU->exJ_~(E(ha;!>RJ`01NhexKQ$s{cW;;GsL8iO2IpKc1Y){"
    b"2N_+@MUW0-fsQpg^6E|U;8skJho2Vc(i@wpYo&V?){h3pIm+refHh4)z!c5*MI$XFFG-U?=M2n&nEtM<a>=Lcz^r"
    b"whfizy>(QPP0gzN*T)h<?`GD3M4F&wmRwA3%LU=FcW0)_NOg&q@WaxRV@qZ(nq$N5_Ihx0P1;1A)OL!j4l0^oUsK"
    b"}0saWqDO9lSa)2jLVxX+Xq0MFpzR1=1m`I>LJn%e!?63Z0`linFC9%8-0=0YH<guvF$yi}9ZW+^e@L>N01=!6Yl5"
    b"ms~ItN=r~XG+3c@C&`ZFa9<`l*O`@0_G=}>u>nf59Ksw4HgaACiz;d0qqb$L8I#C9^*o>=tVuc};FCGPgcBc={H4"
    b"(*O_Lwz6p`-<s+B~(XDzdu*|784QHR_nyp!aF*r*VjO<Lx9X`^>lh_M4Z;(eTI^fj0mTq6ZU>Jp806o(rjxtD33<"
    b"C+4hED?ijjV!XqI$QC98|}oU!MW<uY8)ty7P%IDScU&$%@i5eHzMOn)O`hdbuJZ+Gi@{9qC`eg(4N8PbFPkMXoy3"
    b"P+ehKi7II**MZ@v9BJpi&&V>slVZ~rv&1*!46YNtF3@rL;pm%XdY(R?*gkV+R73Cw6p;gFMaGeKFy$?olML)&SEO"
    b"2Fdvyufu;|y3$pW5Q4x~f?67jdXKh>ABm;e?ahO<HWtQqKr>kDZSi9_zN|eBklk<{GWA9@#Ivtsap(9aSP$k<Ilo"
    b"AhJ_waNA-#BC_A`X0pW9*{tf`mZct5=!wX>Gu|X#hvKk#5p0FM66+B?*J5TCb1<8_datdK9PetL`@m>tr}4pgxZP"
    b"h*s7Q*tw(LDV`|)HN7Pq<EScr@7_>6bA?ZfBDTXdChYv=P}b*f)S^RudCeRSz=eQIi%cZCvj_mgM$S*C4wXgT+|>"
    b"(Sjq6Nr<|Rcw3Qbvv2*h|NS6m8A39-{M~Bbq{dwz|DPX1v&;J6g~k>;smr((d~>?)Qz;c&8MKi89u@(`241Z=}9o"
    b"msQ2x}?@a1oOpk*^4>42u`S<EW3d6rfg9h6gD6y|a+IrVI*LuJj&Nwlx$bU8C;$Mzco;TMmKIC$e=;}{WJfISriB"
    b"Qd2uxhqhFgUvhQ@j>RSkor@`~r6bo7c5LAEACM(p****S+NtDZzbe?1KB=e-v>AJ2iHlE3UcH^=Wgc9d-ikQn4Rm"
    b"uK?yBhiL"
)
_BASE_RESOLVED_FEATURES = (
    b"c-rll&rcIU6vy8d5D+wg0nvjJPexBB9y|~$P%0iM4J9!#CS+`<Wn{ZscBdpH{@9aOP5cLp7Y}mq<Q3yZ{R6z|(Rl"
    b"E}MH3TaeKXxDJ8hS3BNP&y&1R>wv$OB>-gn;2wg3RbP^lO&0!4eqE*7c9-K1^isI#2y_A0+CeKTM~5f2I$aB#sd*"
    b"ZTYl_JL-lpepGkz~!%J<W&{%+kdozXII590N$29Oi!&Q?ms{G*>K;*CS$Pqpa+aVKLwE_>$bx<)gbzlKwup~9AF4"
    b"R0~jYGFjhK)5kxV3oMFV7V=lLy4UMLE4k=vZ5Ih?-lJN)<)@c&KFop~nYSJucww0k=138|-P?&gT5r!d-1rs3Jf;"
    b"u}DfpxdjSSmb263udLM~_ZMP8C;1X9r^}0)y5!>=nj~tuI#^F$BPI1W4FfeZC({$mzjw{)%W!W6gpbwmCJF-UyV{"
    b"&PGH{l?3I4nKR@Lvncmz2By$@3q!#%0Vs{_1jT3|iPcn_vN?6997>X04{%RPju%WK!-p%l_dIFn$c~|xU|AlsGMG"
    b"!~jDp{y5JnCc!hLPJ1@EZ(Lv38Mv#X6L+j0G>v^XmALfOfaES<J<8}%8lj58^Z0m!0D#r(1{AWT!!(TGqKJHI3a`"
    b"A!Hv+hn;0y1@+6m`IZgA?uGIvks1Iy2f_HTAe4(YPqDR^?8h$gSo8?r2x_B;Y;hskYRSs(l<b}u!fd5%Yj1&L6Ex"
    b"n$#|9j_OUsE*vHKiP8~)}4P$&>B2c-HBPg{AnDo>81R|B>R)XR560*y|)f(hL1Z1hhOO|hjfE`5GMVe2W#G-1|N+"
    b"O^w_uCVYMofbBS{&ZQ4oY+3xiGvKEw;5*u77yx4!(cAb>a5ox8Kii#v5%7X5j?Qld{RBcdZ2BWI5a3>w>90tb=b-"
    b"yxuhb>O1upy6~5DbBlg@QeDIQmrw|$rZVXIF9Y>k`C6C3Q?K198!d)CL>}8)EkC!vsu@_68~Bxw1k(NQDyL2{%K!"
    b"29l+!2>Wsw)s(fd2a?7wnE&K$>_x!|w@v(k>8XC_Tj!pn|YmX0jQb+;ft36++5BDA!&Un{FO+7+rL0n-O=A+t((c"
    b"BTH){jC0?>g{g)^sCmytGmM^es&jE{@%^wdr%C`3k|o2<p*rl5VaR{3u&8Ke2!Q-lZHG8sXEyTR~Y_aMw@57xI}c"
    b"Tju!7W!fbD2W~aPX{ne$9`0SBUlgCi?56{xh*6X4dYdsQ`y3(wVP`ViM$F0+>YD+8YiICn;f5d!~PJaN2#tPd"
)
_BASE_BODY_FEATURE = (
    b"c-s5_pOJxwAvfPCu{hN!KczB0nWf?XzyF+`47m&i4EYR23?&Sy3@HqT3{c=81!VwLF<=8lFh+nI1B1zPIWP?aAU;&<e;{W54"
    b"+RVi4f|1zVTH3m@++0@GWKrTc8iH&O&u!(BZ^8!Ft$SCrD8aW5sO1XVkr%543q+pZx|soj$i`-o257V"
)
_BASE_BODY_COUNTERS = {
    0: 0x6B,
    4: 0x12,
    1495: 0x80,
    1690: 0x81,
    1724: 0x83,
    2315: 0x46,
    3483: 0x94,
    3806: 0x97,
    4049: 0x94,
    4376: 0x97,
    5128: 0x52,
    5302: 0x52,
}
_BASE_BIOGRAPHY = (
    b"c-s5_pOJx=AvfPCGe5m3u^^)|KADMufg!++fx+at90Mbe%?ZRjKnxP+Vt{}zsSFJN|NUp+lwd#tAQ4*fS)c#E>KA"
    b"?o=qN)?pqz*^gB3#zLpXycgCBzngFlcJ4CEIxR044cLn=cqgE4~<P=pzz*}>nH6=Ehgc7157bRen%7>XG38Pb7dB"
    b"G5bq1~-OGh8&>T#Xz}Wpk5!KDK0=0{2786yn!ML49-CHMGOTv<T32wfY=iPc5eac@<I@KZ=kzM!0t^1+Frt-2V?~"
    b"Sb%FdBf})2|+(x9q;&!?H1B*pUcNrN9R%MeM-T~`*hzM_lDrSf(u;_x*Uo;r;_#UB)kUa6B1J#qyFKq+%Gec7-P("
    b"Py<M0Ua=n2DGo*j-MHPJUP#gSg5N=&oX5>Pi9n1jI*H4FG46z}x"
)
_HEADER_OBJECTS = (
    (1, "Annotations", False),
    (2, "Front Plane", True),
    (3, "Top Plane", True),
    (4, "Right Plane", True),
    (5, "Origin", True),
    (6, "Lights and Cameras", False),
    (7, "Design Binder", False),
    (8, "Comments", False),
    (9, "Solid Bodies", False),
    (10, "Surface Bodies", False),
    (11, "Material <not specified>", True),
    (12, "Ambient", False),
    (13, "Directional1", False),
    (14, "Directional2", False),
    (15, "Directional3", False),
    (16, "Equations", False),
    (17, "Notes", False),
    (18, "Notes1___EndTag___", False),
    (21, "Markups", False),
    (22, "Sensors", False),
    (23, "Favorites", False),
    (24, "History", False),
    (25, "Selection Sets", False),
)


def encode_native_part(document: CadDocument, model_name: str) -> NativePartStreams:
    object_ids = _write_object_ids(document)
    authored = _write_objects(document, object_ids)
    if not authored and document.brep is not None:
        authored = (
            _WriteObject(
                "brep:imported",
                26,
                "Imported1",
                "Feature",
                "Imported",
                "moBaseBody_c",
            ),
        )
    identity = _native_identity(document, model_name)
    system_features = {
        int(feature.attributes["native_object_id"]): feature
        for feature in document.feature_timeline
        if _is_native_system_feature(feature)
    }
    base = tuple(
        _WriteObject(
            f"base:{object_id}",
            object_id,
            _native_system_name(system_features.get(object_id), name),
            "Sketch" if object_id == 5 else "Feature",
            kind,
            class_name,
        )
        for object_id, name, kind, class_name in _BASE_OBJECTS
    )
    keyword_only = tuple(
        _WriteObject(
            f"base:{object_id}",
            object_id,
            _native_system_name(system_features.get(object_id), name),
            "Feature",
            kind,
            "",
        )
        for object_id, name, kind in _KEYWORD_ONLY_OBJECTS
    )
    objects = (*base, *authored)
    blank_native = not authored and not document.sketches
    keywords = _keywords_payload(
        document,
        model_name,
        (*objects, *keyword_only),
        object_ids,
        identity,
    )
    features = _features_payload(document, model_name, object_ids, identity)
    resolved = (
        _base_record(_BASE_RESOLVED_FEATURES)
        if blank_native
        else _resolved_payload(objects)
    )
    envelope_streams = _native_envelope_streams(
        document,
        model_name,
        identity,
        blank_native,
    )
    parsed = decode_native_model(keywords, resolved)
    capabilities = _proved_write_capabilities(document, authored, parsed, object_ids)
    lanes = tuple(
        (
            object_ids[f"configuration:{configuration.id}"],
            resolved,
        )
        for configuration in document.configurations
    )
    if not lanes:
        lanes = ((0, resolved),)
    return NativePartStreams(
        keywords,
        features,
        resolved,
        lanes,
        capabilities,
        MappingProxyType(object_ids),
        envelope_streams,
    )


def _write_object_ids(document: CadDocument) -> dict[str, int]:
    used = set(range(1, 26))
    result: dict[str, int] = {}
    next_id = 26

    def assign(key: str, native: Any = None) -> int:
        nonlocal next_id
        candidate = native if isinstance(native, int) and native > 25 else None
        if candidate is None or candidate in used or candidate > 0xFFFFFFFE:
            while next_id in used:
                next_id += 1
            candidate = next_id
            next_id += 1
        used.add(candidate)
        result[key] = candidate
        return candidate

    principal = _principal_plane_ids(document.support_planes)
    for plane in document.support_planes:
        key = f"plane:{plane.id}"
        if plane.id in principal:
            result[key] = principal[plane.id]
        else:
            assign(key, plane.attributes.get("native_object_id"))
    for sketch in document.sketches:
        assign(f"sketch:{sketch.id}", sketch.attributes.get("native_object_id"))
    for feature in sorted(document.feature_timeline, key=lambda item: item.order):
        if _is_native_system_feature(feature):
            continue
        native = feature.attributes.get("native_object_id")
        sketch_native = (
            result.get(f"sketch:{feature.sketch_id}")
            if feature.sketch_id is not None
            else None
        )
        if isinstance(native, int) and native == sketch_native:
            result[f"feature:{feature.id}"] = native
        else:
            assign(f"feature:{feature.id}", native)
    configuration_ids: set[int] = set()
    next_configuration_id = 0
    for configuration in document.configurations:
        native = configuration.attributes.get("native_configuration_id")
        candidate = (
            native
            if isinstance(native, int)
            and not isinstance(native, bool)
            and 0 <= native <= 0xFFFFFFFF
            and native not in configuration_ids
            else None
        )
        if candidate is None:
            while next_configuration_id in configuration_ids:
                next_configuration_id += 1
            candidate = next_configuration_id
        configuration_ids.add(candidate)
        result[f"configuration:{configuration.id}"] = candidate
    return result


def _principal_plane_ids(planes: tuple[SupportPlane, ...]) -> dict[str, int]:
    frames = (
        (
            2,
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
            (0.0, 0.0, 1.0),
        ),
        (
            3,
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (0.0, 0.0, -1.0),
            (0.0, 1.0, 0.0),
        ),
        (
            4,
            (0.0, 0.0, 0.0),
            (0.0, 0.0, -1.0),
            (0.0, 1.0, 0.0),
            (1.0, 0.0, 0.0),
        ),
    )
    result: dict[str, int] = {}
    for plane in planes:
        transform = plane.transform
        values = (
            (transform.origin.x, transform.origin.y, transform.origin.z),
            (transform.x_axis.x, transform.x_axis.y, transform.x_axis.z),
            (transform.y_axis.x, transform.y_axis.y, transform.y_axis.z),
            (transform.z_axis.x, transform.z_axis.y, transform.z_axis.z),
        )
        for object_id, *frame in frames:
            if all(
                math.isclose(left, right, rel_tol=0.0, abs_tol=1e-9)
                for left_vector, right_vector in zip(values, frame, strict=True)
                for left, right in zip(left_vector, right_vector, strict=True)
            ):
                result[plane.id] = object_id
                break
    return result


def _write_objects(
    document: CadDocument, object_ids: dict[str, int]
) -> tuple[_WriteObject, ...]:
    parameters = {parameter.id: parameter for parameter in document.parameters}
    result: list[_WriteObject] = []
    for plane in document.support_planes:
        object_id = object_ids[f"plane:{plane.id}"]
        if object_id in {2, 3, 4}:
            continue
        dimensions = _write_dimensions(
            plane.id,
            (plane.offset_parameter_id,) if plane.offset_parameter_id else (),
            parameters,
        )
        result.append(
            _WriteObject(
                plane.id,
                object_id,
                plane.name,
                "Feature",
                "Plane",
                "moRefPlane_c",
                dimensions=dimensions,
                payload=_plane_payload(plane),
            )
        )
    sketches = {sketch.id: sketch for sketch in document.sketches}
    emitted_sketches: set[str] = set()
    for feature in sorted(document.feature_timeline, key=lambda item: item.order):
        if _is_native_system_feature(feature):
            continue
        if feature.sketch_id is not None and feature.sketch_id in sketches:
            sketch = sketches[feature.sketch_id]
            if sketch.id not in emitted_sketches:
                result.append(_write_sketch(sketch, parameters, object_ids, feature))
                emitted_sketches.add(sketch.id)
        feature_id = object_ids[f"feature:{feature.id}"]
        if any(item.object_id == feature_id for item in result):
            continue
        result.append(_write_feature(feature, parameters, object_ids))
    for sketch in document.sketches:
        if sketch.id not in emitted_sketches:
            result.append(_write_sketch(sketch, parameters, object_ids))
    return tuple(result)


def _is_native_system_feature(feature: FeatureStep) -> bool:
    native_id = feature.attributes.get("native_object_id")
    return (
        isinstance(native_id, int)
        and not isinstance(native_id, bool)
        and native_id in _SYSTEM_OBJECT_IDS
        and str(feature.kind).casefold()
        in {FeatureKind.NATIVE.value, FeatureKind.REFERENCE.value}
    )


def _native_system_name(feature: FeatureStep | None, fallback: str) -> str:
    if feature is None:
        return fallback
    properties = feature.attributes.get("native_properties")
    if isinstance(properties, Mapping):
        name = properties.get("Name")
        if isinstance(name, str):
            return name
    return feature.name or fallback


def _write_sketch(
    sketch: Sketch,
    parameters: dict[str, Parameter],
    object_ids: dict[str, int],
    native_feature: FeatureStep | None = None,
) -> _WriteObject:
    object_id = object_ids[f"sketch:{sketch.id}"]
    dimensions = list(_write_dimensions(sketch.id, sketch.parameter_ids, parameters))
    payload, generated_dimensions = _sketch_payload(sketch, object_id, object_ids)
    existing = {dimension.name for dimension in dimensions}
    dimensions.extend(
        dimension
        for dimension in generated_dimensions
        if dimension.name not in existing
    )
    native_properties = (
        _native_keyword_properties(native_feature.attributes)
        if native_feature is not None
        else None
    )
    return _WriteObject(
        sketch.id,
        object_id,
        sketch.name,
        "Sketch",
        "Sketch",
        "moProfileFeature_c",
        (
            (("Dissectable", "true"),)
            if native_properties is None
            else native_properties
        ),
        tuple(dimensions),
        payload,
    )


def _write_feature(
    feature: FeatureStep,
    parameters: dict[str, Parameter],
    object_ids: dict[str, int],
) -> _WriteObject:
    object_id = object_ids[f"feature:{feature.id}"]
    dimensions = list(_write_dimensions(feature.id, feature.parameter_ids, parameters))
    tag, kind, class_name = _write_feature_type(feature)
    native_properties = _native_keyword_properties(feature.attributes)
    properties = list(native_properties or ())
    payload = b""
    if tag == "Extrusion":
        if native_properties is None and feature.sketch_id is not None:
            child = object_ids.get(f"sketch:{feature.sketch_id}")
            if child is not None:
                properties.extend(
                    (
                        ("Dissectable", "true"),
                        ("DissectableChildren", str(child)),
                        ("DissectableRoot", "true"),
                    )
                )
        generated = _definition_dimension(feature)
        if generated is not None and not dimensions:
            dimensions.append(generated)
        payload = _extrusion_payload(feature)
    elif kind == "Fillet":
        generated = _definition_dimension(feature)
        if generated is not None and not dimensions:
            dimensions.append(generated)
        payload = _fillet_payload(feature, object_ids)
    return _WriteObject(
        feature.id,
        object_id,
        feature.name,
        tag,
        kind,
        class_name,
        tuple(properties),
        tuple(dimensions),
        payload,
    )


def _native_keyword_properties(
    attributes: Mapping[str, Any],
) -> tuple[tuple[str, str], ...] | None:
    properties = attributes.get("native_properties")
    if not isinstance(properties, Mapping):
        return None
    return tuple(
        (name, value)
        for name, value in properties.items()
        if isinstance(name, str)
        and isinstance(value, str)
        and name not in {"id", "Name"}
    )


def _write_feature_type(feature: FeatureStep) -> tuple[str, str, str]:
    kind = str(feature.kind).casefold()
    if kind == FeatureKind.EXTRUSION.value:
        class_name = (
            "moCut_c"
            if feature.operation == BooleanOperation.CUT
            or str(feature.operation).casefold() == BooleanOperation.CUT.value
            else "moExtrusion_c"
        )
        return "Extrusion", "Extrusion", class_name
    if kind == FeatureKind.FILLET.value:
        return "Feature", "Fillet", "Fillet_c"
    native = feature.attributes.get("native_type")
    if isinstance(native, str) and native.strip():
        if native.strip().casefold() in {"basebody", "imported"}:
            return "Feature", "Imported", "moBaseBody_c"
        return "Feature", native.strip(), "moCompFeature_c"
    names = {
        FeatureKind.REVOLUTION.value: ("Revolution", "moRevolution_c"),
        FeatureKind.SWEEP.value: ("Sweep", "moSweep_c"),
        FeatureKind.LOFT.value: ("Blend", "moBlend_c"),
        FeatureKind.HOLE.value: ("HoleWizard", "moHoleWzd_c"),
        FeatureKind.CHAMFER.value: ("Chamfer", "moChamfer_c"),
        FeatureKind.SHELL.value: ("Shell", "moShell_c"),
        FeatureKind.PATTERN.value: ("Pattern", "moLPattern_c"),
        FeatureKind.MIRROR.value: ("MirrorPattern", "moMirrorPattern_c"),
        FeatureKind.BOOLEAN.value: ("Combine", "moCombineBodies_c"),
    }
    native_kind, class_name = names.get(kind, (str(feature.kind), "moCompFeature_c"))
    return "Feature", native_kind, class_name


def _write_dimensions(
    owner_id: str,
    parameter_ids: tuple[str | None, ...],
    parameters: dict[str, Parameter],
) -> tuple[_WriteDimension, ...]:
    selected: list[Parameter] = []
    seen: set[str] = set()
    for parameter_id in parameter_ids:
        if parameter_id is None or parameter_id in seen:
            continue
        parameter = parameters.get(parameter_id)
        if parameter is not None:
            selected.append(parameter)
            seen.add(parameter_id)
    for parameter in parameters.values():
        if parameter.owner_id == owner_id and parameter.id not in seen:
            selected.append(parameter)
            seen.add(parameter.id)
    return tuple(
        dimension
        for parameter in selected
        if (dimension := _parameter_dimension(parameter)) is not None
    )


def _parameter_dimension(parameter: Parameter) -> _WriteDimension | None:
    value = parameter.value.value
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or parameter.value.kind is not ValueKind.LENGTH
    ):
        return None
    factor = {
        "": 1.0,
        "mm": 1.0,
        "millimeter": 1.0,
        "millimeters": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "inch": 25.4,
        "inches": 25.4,
    }.get(parameter.value.unit.casefold())
    number = float(value)
    if factor is None or not math.isfinite(number):
        return None
    millimeters = number * factor
    source_text = parameter.attributes.get("source_text")
    text = (
        source_text
        if isinstance(source_text, str) and source_text
        else format(millimeters, ".15g")
    )
    return _WriteDimension(
        parameter.name,
        millimeters,
        text,
        parameter.role,
    )


def _definition_dimension(feature: FeatureStep) -> _WriteDimension | None:
    definition = feature.definition
    value = None
    prefix = ""
    if isinstance(definition, ExtrusionFeature):
        value = definition.length
    elif isinstance(definition, FilletFeature):
        value = definition.radius
        prefix = "R"
    if value is None:
        return None
    parameter = Parameter("", "D1", value)
    dimension = _parameter_dimension(parameter)
    if dimension is None:
        return None
    return replace(dimension, text=prefix + dimension.text)


def _plane_payload(plane: SupportPlane) -> bytes:
    transform = plane.transform
    origin = (transform.origin.x, transform.origin.y, transform.origin.z)
    x_axis = (transform.x_axis.x, transform.x_axis.y, transform.x_axis.z)
    y_axis = (transform.y_axis.x, transform.y_axis.y, transform.y_axis.z)
    z_axis = (transform.z_axis.x, transform.z_axis.y, transform.z_axis.z)
    vectors = (x_axis, y_axis, z_axis)
    if not _orthonormal(vectors) or not all(
        math.isfinite(value) for vector in (origin, *vectors) for value in vector
    ):
        return b""
    frame = bytearray(121)
    struct.pack_into("<3d", frame, 0, *(value / 1000.0 for value in origin))
    struct.pack_into("<3d", frame, 24, *z_axis)
    frame[48] = 1
    rows = tuple(zip(x_axis, y_axis, z_axis, strict=True))
    for index, row in enumerate(rows):
        struct.pack_into("<3d", frame, 49 + index * 24, *row)
    return _class_declaration("moFixedRefPlnData_c") + bytes(frame)


def _orthonormal(vectors: tuple[tuple[float, float, float], ...]) -> bool:
    return all(
        math.isclose(_norm(vector), 1.0, abs_tol=1e-9) for vector in vectors
    ) and all(
        math.isclose(_dot(left, right), 0.0, abs_tol=1e-9)
        for left, right in itertools.combinations(vectors, 2)
    )


def _sketch_payload(
    sketch: Sketch, object_id: int, object_ids: dict[str, int]
) -> tuple[bytes, tuple[_WriteDimension, ...]]:
    payload = bytearray()
    plane_id = object_ids.get(f"plane:{sketch.support_plane_id}", 2)
    payload.extend(_plane_reference(plane_id))
    generated: list[_WriteDimension] = []
    consumed: set[str] = set()
    local_id = 1
    entities = {entity.id: entity for entity in sketch.entities}
    for profile in sketch.closed_profile_entity_ids:
        selected = tuple(entities.get(entity_id) for entity_id in profile)
        if len(selected) == 4 and all(
            entity is not None and isinstance(entity.geometry, LineGeometry)
            for entity in selected
        ):
            rectangle = _rectangle_coordinates(
                tuple(entity.geometry for entity in selected if entity is not None)
            )
            if rectangle is not None:
                points = (
                    (rectangle[0], rectangle[1]),
                    (rectangle[2], rectangle[1]),
                    (rectangle[2], rectangle[3]),
                    (rectangle[0], rectangle[3]),
                )
                for point in points:
                    payload.extend(_coordinate_marker(point, local_id, _POINT_LOCUS))
                    local_id += 1
                for start, end in ((0, 1), (1, 2), (2, 3), (3, 0)):
                    payload.extend(_line_marker(start, end, local_id))
                    local_id += 1
                consumed.update(profile)
                continue
        if (
            len(selected) == 1
            and selected[0] is not None
            and isinstance(selected[0].geometry, CircleGeometry)
        ):
            circle = selected[0].geometry
            center = (circle.center.x, circle.center.y)
            radial = (circle.center.x + circle.radius, circle.center.y)
            payload.extend(_coordinate_marker(center, local_id, _CIRCLE_LOCUS))
            local_id += 1
            payload.extend(_coordinate_marker(radial, local_id, _POINT_LOCUS))
            local_id += 1
            generated.append(
                _WriteDimension(
                    f"D{len(generated) + 1}",
                    circle.radius,
                    "R" + format(circle.radius, ".15g"),
                    ParameterRole.DRIVING,
                )
            )
            consumed.add(selected[0].id)
    for entity in sketch.entities:
        if entity.id in consumed:
            continue
        if isinstance(entity.geometry, LineGeometry):
            start_index = local_id
            payload.extend(
                _coordinate_marker(
                    (entity.geometry.start.x, entity.geometry.start.y),
                    local_id,
                    _POINT_LOCUS,
                )
            )
            local_id += 1
            payload.extend(
                _coordinate_marker(
                    (entity.geometry.end.x, entity.geometry.end.y),
                    local_id,
                    _POINT_LOCUS,
                )
            )
            local_id += 1
            roster_start = start_index - 1
            payload.extend(_line_marker(roster_start, roster_start + 1, local_id))
            local_id += 1
        elif isinstance(entity.geometry, CircleGeometry):
            center = (entity.geometry.center.x, entity.geometry.center.y)
            radial = (center[0] + entity.geometry.radius, center[1])
            payload.extend(_coordinate_marker(center, local_id, _CIRCLE_LOCUS))
            local_id += 1
            payload.extend(_coordinate_marker(radial, local_id, _POINT_LOCUS))
            local_id += 1
            generated.append(
                _WriteDimension(
                    f"D{len(generated) + 1}",
                    entity.geometry.radius,
                    "R" + format(entity.geometry.radius, ".15g"),
                    ParameterRole.DRIVING,
                )
            )
    return bytes(payload), tuple(generated)


def _plane_reference(object_id: int) -> bytes:
    block = bytearray(67)
    struct.pack_into("<I", block, 0, object_id)
    block[4] = 1
    block[8:12] = b"\0\0\x03\0"
    struct.pack_into("<d", block, 39, 1.0)
    block[50] = 2
    block[54] = 0xFF
    block[55:58] = b"\xff\xff\xff"
    return bytes(block)


def _coordinate_marker(
    point: tuple[float, float], local_id: int, locus: bytes
) -> bytes:
    record = bytearray(142)
    record[:5] = _CURRENT_MARKER
    record[5:13] = b"\xff" * 8
    record[13:17] = b"\0\0\x80\xbf"
    struct.pack_into("<I", record, 17, 1)
    record[23:27] = locus
    struct.pack_into("<H", record, 27, 1)
    record[31:39] = b"\0\0\x80\xbf\0\0\x04\0"
    struct.pack_into("<d", record, 48, 1.0)
    record[56:58] = _COORDINATE_TAG
    struct.pack_into("<2d", record, 58, point[0] / 1000.0, point[1] / 1000.0)
    struct.pack_into("<I", record, 138, local_id)
    return bytes(record)


def _line_marker(start: int, end: int, local_id: int) -> bytes:
    record = bytearray(92)
    record[:5] = _CURRENT_MARKER
    record[5:13] = b"\xff" * 8
    record[13:17] = b"\0\0\x80\xbf"
    struct.pack_into("<I", record, 17, 2)
    record[23:27] = _POINT_LOCUS
    struct.pack_into("<H", record, 27, 1)
    struct.pack_into("<d", record, 48, 1.0)
    struct.pack_into("<HH", record, 64, start, end)
    struct.pack_into("<I", record, 88, local_id)
    return bytes(record)


def _rectangle_coordinates(
    lines: tuple[LineGeometry, ...],
) -> tuple[float, float, float, float] | None:
    points = tuple((line.start.x, line.start.y) for line in lines)
    ends = tuple((line.end.x, line.end.y) for line in lines)
    if any(ends[index] != points[(index + 1) % 4] for index in range(4)):
        return None
    xs = sorted({point[0] for point in points})
    ys = sorted({point[1] for point in points})
    if len(xs) != 2 or len(ys) != 2:
        return None
    if set(points) != {(x, y) for x in xs for y in ys}:
        return None
    return xs[0], ys[0], xs[1], ys[1]


def _extrusion_payload(feature: FeatureStep) -> bytes:
    definition = feature.definition
    direction = int(isinstance(definition, ExtrusionFeature) and definition.reversed)
    condition = (
        definition.end_condition if isinstance(definition, ExtrusionFeature) else None
    )
    termination = {
        ExtrusionEndCondition.BLIND: 0,
        ExtrusionEndCondition.THROUGH_ALL: 1,
        ExtrusionEndCondition.UP_TO_FIRST: 2,
        ExtrusionEndCondition.UP_TO_VERTEX: 3,
        ExtrusionEndCondition.UP_TO_FACE: 4,
        ExtrusionEndCondition.UP_TO_SHAPE: 4,
        ExtrusionEndCondition.OFFSET_FROM_SURFACE: 5,
        ExtrusionEndCondition.MID_PLANE: 6,
    }.get(condition, 0)
    declaration = _class_declaration("moEndSpec_c")
    return b"".join(
        (
            declaration,
            b"\0\0",
            struct.pack("<II", 1, 0),
            struct.pack("<I", direction),
            b"\0\0",
            struct.pack("<II", termination, 0),
        )
    )


def _fillet_payload(feature: FeatureStep, object_ids: dict[str, int]) -> bytes:
    result = bytearray()
    for selection_id in feature.selection_ids:
        producer = 0
        local_id = 0
        parts = selection_id.rsplit(":", 1)
        if len(parts) == 2:
            try:
                local_id = int(parts[1])
            except ValueError:
                local_id = 0
        if feature.input_feature_ids:
            producer = object_ids.get(f"feature:{feature.input_feature_ids[-1]}", 0)
        if producer and local_id:
            record = bytearray(38)
            record[:16] = _EDGE_SELECTION_IDENTITY
            struct.pack_into("<I", record, 26, producer)
            struct.pack_into("<I", record, 34, local_id)
            result.extend(record)
    return bytes(result)


def _keywords_payload(
    document: CadDocument,
    model_name: str,
    objects: tuple[_WriteObject, ...],
    object_ids: Mapping[str, int],
    identity: _NativeIdentity,
) -> bytes:
    children: list[str] = []
    configurations = document.configurations or ()
    for configuration in configurations:
        configuration_id = object_ids[f"configuration:{configuration.id}"]
        attributes = {
            "id": str(configuration_id),
            "Name": configuration.name,
            "Type": "ConfigurationManager",
        }
        native_properties = configuration.attributes.get("native_properties")
        material = (
            native_properties.get("Material")
            if isinstance(native_properties, Mapping)
            else configuration.attributes.get("Material")
        )
        if isinstance(material, str):
            attributes["Material"] = material
        else:
            attributes["Material"] = "Material <not specified>"
        children.append(_xml_element("Configuration", attributes))
    if not configurations:
        children.append(
            _xml_element(
                "Configuration",
                {
                    "id": "0",
                    "Name": "Default",
                    "Type": "ConfigurationManager",
                    "Material": "Material <not specified>",
                },
            )
        )
    for item in sorted(
        objects, key=lambda value: (value.xml_tag, str(value.object_id))
    ):
        attributes = {"id": str(item.object_id), "Name": item.name}
        if item.xml_tag == "Feature" or item.kind == "Origin":
            attributes["Type"] = item.kind
        attributes.update(item.properties)
        dimensions = "".join(
            _xml_element(
                "Dimension",
                {"Name": dimension.name},
                _xml_text(dimension.text),
            )
            for dimension in item.dimensions
        )
        children.append(
            _xml_element(
                item.xml_tag,
                attributes,
                dimensions if item.dimensions else None,
            )
        )
    root = _xml_element(
        "Keywords",
        {"id": str(identity.creation_stamp), "Name": identity.reference_name},
        "".join(children),
    )
    return b"\x86" + _xml_document(root)


def _features_payload(
    document: CadDocument,
    model_name: str,
    object_ids: Mapping[str, int],
    identity: _NativeIdentity,
) -> bytes:
    header = _xml_element(
        "swHeader",
        {"swObjCount": "1"},
        _xml_element(
            "swFile",
            {
                "id": "3",
                "swDocType": "PART",
                "swCreationTime": str(identity.creation_stamp),
                "swPath": f"{model_name}{PART_SUFFIX}",
            },
        ),
    )
    active = next(
        (
            configuration
            for configuration in document.configurations
            if configuration.active
        ),
        document.configurations[0] if document.configurations else None,
    )
    active_name = active.name if active is not None else "Default"
    active_id = 0
    if active is not None:
        active_id = object_ids[f"configuration:{active.id}"]
    models = _xml_element(
        "swModelList",
        {"swObjCount": "1"},
        _xml_element(
            "swModel",
            {
                "id": "2",
                "swName": model_name,
                "swConfigurationName": active_name,
                "swConfigurationId": str(active_id),
                "swLastModifiedStamp": str(identity.last_modified_stamp),
                "swConfigurationFlags": str(identity.configuration_flags),
                "swFileRef": "3",
            },
        ),
    )
    configurations = document.configurations or ()
    configuration_children: list[str] = []
    if configurations:
        for index, configuration in enumerate(configurations, start=1):
            native_id = object_ids[f"configuration:{configuration.id}"]
            configuration_children.append(
                _xml_element(
                    "swConfiguration",
                    {
                        "id": str(index),
                        "swName": configuration.name,
                        "swID": str(native_id),
                        "swReference": identity.reference_name,
                        "swMostRecentConfiguration": (
                            "YES" if configuration.active else "NO"
                        ),
                        "swConfigurationNeedsUpdate": "NO",
                        "swDefeatureConfiguration": "NO",
                        "swModelRef": "2",
                    },
                )
            )
    else:
        configuration_children.append(
            _xml_element(
                "swConfiguration",
                {
                    "id": "1",
                    "swName": "Default",
                    "swID": "0",
                    "swReference": identity.reference_name,
                    "swMostRecentConfiguration": "YES",
                    "swConfigurationNeedsUpdate": "NO",
                    "swDefeatureConfiguration": "NO",
                    "swModelRef": "2",
                },
            )
        )
    configuration_list = _xml_element(
        "swConfigurationList",
        {"swObjCount": str(len(configurations) or 1)},
        "".join(configuration_children),
    )
    root = _xml_element(
        "swSolidWorks",
        {
            "xmlns": _SOLIDWORKS_XML_NAMESPACE,
            "swObjCount": "3",
            "swVersion": "18000",
        },
        "".join(
            (
                header,
                models,
                configuration_list,
                _xml_element("swExtFeatureList", {"swObjCount": "0"}),
            )
        ),
    )
    return _xml_document(root)


def _xml_document(root: str) -> bytes:
    return ('<?xml version="1.0" encoding="UTF-8"?>\r\n' + root + "\r\n").encode(
        "utf-8"
    )


def _xml_element(
    name: str,
    attributes: Mapping[str, str],
    body: str | None = None,
) -> str:
    encoded_attributes = "".join(
        f' {key}="{_xml_attribute(value)}"' for key, value in attributes.items()
    )
    if body is None:
        return f"<{name}{encoded_attributes}/>"
    return f"<{name}{encoded_attributes}>{body}</{name}>"


def _xml_attribute(value: str) -> str:
    return (
        _xml_text(value)
        .replace('"', "&quot;")
        .replace("\t", "&#9;")
        .replace("\n", "&#10;")
        .replace("\r", "&#13;")
    )


def _xml_text(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _resolved_payload(objects: tuple[_WriteObject, ...]) -> bytes:
    authored = objects[len(_BASE_OBJECTS) :]
    if (
        len(authored) == 1
        and authored[0].object_id == 26
        and authored[0].name == "Imported1"
        and authored[0].class_name == "moBaseBody_c"
        and not authored[0].dimensions
        and not authored[0].payload
    ):
        return _base_body_payload()
    output = bytearray(struct.pack("<IH", len(objects), max(0, len(objects) - 1)))
    for item in objects:
        output.extend(_class_declaration(item.class_name))
        operation = item.kind == "Extrusion"
        operation_code = 2 if item.class_name == "moCut_c" else 0
        output.extend(
            _name_record(
                item.name,
                item.object_id,
                operation=operation,
                operation_code=operation_code,
            )
        )
        output.extend(item.payload)
        for dimension in item.dimensions:
            output.extend(_scalar_record(dimension))
    return bytes(output)


def _base_body_payload() -> bytes:
    output = bytearray(_base_record(_BASE_RESOLVED_FEATURES))
    for offset, value in _BASE_BODY_COUNTERS.items():
        output[offset] = value
    return bytes(output[:-4]) + _base_record(_BASE_BODY_FEATURE) + bytes(output[-4:])


def _class_declaration(name: str) -> bytes:
    encoded = name.encode("ascii")
    return CLASS_MARKER + struct.pack("<H", len(encoded)) + encoded


def _name_record(
    name: str, object_id: int, *, operation: bool = False, operation_code: int = 0
) -> bytes:
    encoded = name.encode("utf-16le")
    units = len(encoded) // 2
    if not 1 <= units <= 255:
        raise SldprtFormatError(
            "native SOLIDWORKS object name exceeds 255 UTF-16 units"
        )
    fields = (
        b"\0" * 4 + struct.pack("<HBBI", 0x0140, operation_code, 0x40, object_id)
        if operation
        else struct.pack("<dI", 2.0, object_id)
    )
    return _NAME_PREFIX + bytes((units,)) + encoded + fields + b"\0" * 16


def _scalar_record(dimension: _WriteDimension) -> bytes:
    encoded = dimension.name.encode("utf-16le")
    units = len(encoded) // 2
    if not 1 <= units <= 255:
        raise SldprtFormatError(
            "native SOLIDWORKS dimension name exceeds 255 UTF-16 units"
        )
    trailer = bytearray(51)
    trailer[3:7] = b"\xff" * 4
    trailer[21:27] = b"\x01\0\0\0\x02\0"
    trailer[27] = 1 if dimension.role is ParameterRole.DRIVEN else 0
    return b"".join(
        (
            _class_declaration("moLengthParameter_c"),
            _NAME_PREFIX,
            bytes((units,)),
            encoded,
            _SCALAR_HEADER,
            struct.pack("<d", dimension.value_mm / 1000.0),
            bytes(trailer),
        )
    )


def _native_identity(document: CadDocument, model_name: str) -> _NativeIdentity:
    authored = sum(
        not _is_native_system_feature(feature) for feature in document.feature_timeline
    )
    if authored == 0 and not document.sketches:
        return _NativeIdentity(
            1785690802,
            114,
            101,
            1785690807,
            _SOLIDWORKS_CONFIGURATION_FLAGS,
            "Part1",
        )
    creation_stamp = _stable_u32(document, model_name)
    last_modified_stamp = 101 + authored * 4 + len(document.sketches) * 2
    return _NativeIdentity(
        creation_stamp,
        last_modified_stamp,
        101,
        (creation_stamp + authored * 7 + len(document.sketches) * 3 + 5) & 0x7FFFFFFF,
        _SOLIDWORKS_CONFIGURATION_FLAGS,
        "Part1",
    )


def _native_envelope_streams(
    document: CadDocument,
    model_name: str,
    identity: _NativeIdentity,
    blank_native: bool,
) -> Mapping[str, bytes]:
    configuration_name = next(
        (
            configuration.name
            for configuration in document.configurations
            if configuration.active
        ),
        document.configurations[0].name if document.configurations else "Default",
    )
    zero = struct.pack("<I", 0)
    streams = {
        "Contents/CMgrHdr2": _configuration_header_payload(
            configuration_name, identity
        ),
        "Contents/CnfgObjs": zero + _serialized_string("") + _serialized_string(""),
        "Contents/CusProps": _custom_properties_payload(),
        "Contents/OleItems": zero,
        "Contents/eModelLic": zero,
        "ModelStamps": struct.pack(
            "<III",
            identity.creation_stamp,
            identity.last_modified_stamp,
            identity.baseline_stamp,
        ),
        "_MO_VERSION_18000/Biography": _biography_payload(model_name, identity),
        "_MO_VERSION_18000/History": _version_history_payload(),
    }
    if blank_native:
        model_header = _model_header_payload(identity, configuration_name)
        streams.update(
            {
                "Contents/CMgr": _base_record(_BASE_CONFIGURATION_MANAGER),
                "Contents/Config-0": _base_record(_BASE_CONFIGURATION),
                "Contents/Config-0-LWDATA": _base_record(_BASE_LIGHTWEIGHT_DATA),
                "Contents/Config-0-ModelHeader": model_header,
                "Contents/Definition": _base_record(_BASE_DEFINITION),
                "Header2": model_header,
            }
        )
    return MappingProxyType(streams)


def _base_record(chunks: bytes | tuple[bytes, ...]) -> bytes:
    encoded = chunks if isinstance(chunks, bytes) else b"".join(chunks)
    return zlib.decompress(base64.b85decode(encoded))


def _model_header_payload(
    identity: _NativeIdentity,
    configuration_name: str,
    user_name: str = "Kit",
) -> bytes:
    legacy_stamp = bytes.fromhex("f65a1a69")
    output = bytearray(_class_declaration("moHeader_c"))
    output.extend(
        bytes.fromhex("01000000ffff00000f00")
        + b"su_CStringArray"
        + struct.pack("<H", 1)
    )
    output.extend(_serialized_string(user_name))
    output.extend(bytes.fromhex("03800100"))
    output.extend(_serialized_string(""))
    output.extend(_class_declaration("suObList"))
    output.extend(struct.pack("<H", 24))
    output.extend(_class_declaration("moLogs_c"))
    output.extend(struct.pack("<H", 1))
    output.extend(_class_declaration("moStamp_c"))
    output.extend(b"\0" * 6 + legacy_stamp)
    output.extend(_serialized_string("Created"))
    output.extend(struct.pack("<I", 0))
    output.extend(_serialized_string("Part1"))
    for object_id, name, modified in _HEADER_OBJECTS:
        actions = ("Created", "Modified") if modified else ("Created",)
        output.extend(bytes.fromhex("0880") + struct.pack("<H", len(actions)))
        stamp = (
            legacy_stamp
            if object_id <= 16
            else struct.pack("<I", identity.creation_stamp)
        )
        for index, action in enumerate(actions):
            output.extend(
                bytes.fromhex("0a80") + struct.pack("<I", index) + b"\0\0" + stamp
            )
            output.extend(_serialized_string(action))
        output.extend(struct.pack("<I", object_id))
        output.extend(_serialized_string(name))
    output.extend(
        legacy_stamp
        + struct.pack("<IH", 26, 0)
        + struct.pack("<I", identity.last_modified_stamp)
    )
    output.extend(_class_declaration("moExtObject_c"))
    output.extend(_class_declaration("moCStringHandle_c"))
    output.extend(_serialized_string(""))
    output.extend(bytes.fromhex("4180"))
    output.extend(_serialized_string(identity.reference_name))
    output.extend(bytes.fromhex("020000"))
    output.extend(struct.pack("<I", identity.creation_stamp))
    output.extend(_serialized_string("") * 3)
    output.extend(bytes.fromhex("0008"))
    output.extend(struct.pack("<III", identity.header_stamp, 1, 0))
    output.extend(struct.pack("<I", 0xFFFFFFFF))
    output.extend(_serialized_string(configuration_name))
    output.extend(b"\0" * 16)
    output.extend(struct.pack("<I", identity.baseline_stamp))
    output.extend(b"\0" * 8)
    output.extend(struct.pack("<I", identity.creation_stamp))
    output.extend(b"\0" * 22)
    output.extend(struct.pack("<I", identity.header_stamp))
    output.extend(bytes.fromhex("0680"))
    output.extend(b"\0" * 14 + b"\xff" * 10)
    output.extend(_class_declaration(""))
    output.extend(b"\0" * 40)
    output.extend(struct.pack("<I", 1))
    output.extend(b"\0" * 16)
    output.extend(struct.pack("<I", 1))
    return bytes(output)


def _configuration_header_payload(
    configuration_name: str, identity: _NativeIdentity
) -> bytes:
    return b"".join(
        (
            _class_declaration("dmConfigMgrHeader_c"),
            struct.pack("<H", 1),
            _class_declaration("dmConfigHeader_c"),
            struct.pack("<I", 1),
            _serialized_string(configuration_name),
            struct.pack("<II", 0, identity.last_modified_stamp),
            _serialized_string(configuration_name),
            struct.pack("<II", 0xFFFFFFFF, 0),
            _serialized_string(""),
            _serialized_string(""),
            struct.pack(
                "<IIIIII",
                identity.configuration_flags & 0xFFFFFFFF,
                0,
                identity.baseline_stamp,
                identity.baseline_stamp,
                identity.header_stamp,
                2,
            ),
        )
    )


def _custom_properties_payload() -> bytes:
    return b"".join(
        (
            _class_declaration("moCusPropMgr_c"),
            struct.pack("<H", 0xFFFF),
            _class_declaration(""),
            struct.pack("<II", 1, 0),
            _class_declaration("moCusPropContainer_c"),
            _class_declaration("moFilePropContainer_c"),
            b"\0" * 13,
        )
    )


def _version_history_payload() -> bytes:
    return b"".join(
        (
            _class_declaration("moVersionHistory_c"),
            struct.pack("<IIH", 1, 0, 0),
            bytes.fromhex("f65a1a69"),
            _serialized_string(""),
            b"PF\0\0",
            _class_declaration("moDateCodeHistory_c"),
            struct.pack("<I", 1),
            bytes.fromhex("34e71e"),
            struct.pack("<IBI", 1, 0, 0xFFFFFFFF),
            b"\0" * 14,
        )
    )


def _biography_payload(model_name: str, identity: _NativeIdentity) -> bytes:
    filetime = 116444736000000000 + identity.creation_stamp * 10_000_000
    first_paths = (
        "C:\\Windows\\System32\\",
        "C:\\Windows\\",
        "C:\\Program Files\\SOLIDWORKS\\",
        "C:\\Temp\\",
        "C:\\Temp\\",
        "C:\\Kit\\Part.PRTDOT",
    )
    second_paths = (
        "C:\\Windows\\System32\\",
        "C:\\Windows\\",
        "C:\\",
        "C:\\Temp\\",
        "C:\\Temp\\",
        "C:\\Kit\\Part.PRTDOT",
    )
    output = bytearray(
        _class_declaration("moBiography_c")
        + bytes.fromhex(
            "020000005046000034e71e0001000000090000000c000000020000000a00000000000000f4650000"
        )
    )
    for _ in range(7):
        output.extend(_serialized_string(""))
        output.extend(b"\0" * (14 if len(output) == 63 else 12))
    output.extend(struct.pack("<QI", filetime, 0x29310000))
    for path in first_paths:
        output.extend(_serialized_string(path))
        output.extend(bytes.fromhex("0300000000404f4505000000"))
    output.extend(
        bytes.fromhex(
            "5046000034e71e0001000000090000000c000000020000000a0000000000000058660000"
        )
    )
    output.extend(_serialized_string(""))
    output.extend(struct.pack("<HQI", 0x1809, filetime, 0x6BAA7000))
    for path in second_paths:
        output.extend(_serialized_string(path))
        output.extend(bytes.fromhex("030000000050af0c05000000"))
    output.extend(struct.pack("<QI", filetime, 0x55820000))
    for value in ("*", "*", "C:\\", "*", "*"):
        output.extend(_serialized_string(value))
        output.extend(bytes.fromhex("030000000090a20c05000000"))
    output.extend(_serialized_string(f"C:\\{model_name}.sldprt"))
    output.extend(bytes.fromhex("030000000090a20c05000000"))
    return bytes(output)


def _serialized_string(value: str) -> bytes:
    encoded = value.encode("utf-16le")
    units = len(encoded) // 2
    if units > 0xFE:
        raise SldprtFormatError(
            "native SOLIDWORKS serialized string exceeds 254 UTF-16 units"
        )
    return bytes.fromhex("fffeff") + bytes((units,)) + encoded


def _stable_u32(document: CadDocument, model_name: str, domain: bytes = b"") -> int:
    source = (
        model_name.encode("utf-8")
        + b"\0"
        + document.to_json(indent=None).encode("utf-8")
    )
    if domain:
        source += b"\0" + domain
    digest = hashlib.sha256(source).digest()
    value = int.from_bytes(digest[:4], "little") & 0x7FFFFFFF
    return value or 1


def _proved_write_capabilities(
    document: CadDocument,
    authored: tuple[_WriteObject, ...],
    parsed: NativeModel,
    object_ids: dict[str, int],
) -> frozenset[Capability]:
    result: set[Capability] = set()
    if all(
        configuration.parent_id is None
        and not configuration.overrides
        and not configuration.suppressed_feature_ids
        for configuration in document.configurations
    ) and (
        not document.configurations
        or sum(configuration.active for configuration in document.configurations) == 1
    ):
        expected = tuple(
            (
                configuration.name,
                object_ids[f"configuration:{configuration.id}"],
            )
            for configuration in document.configurations
        )
        actual = tuple(
            (configuration.name, configuration.configuration_id)
            for configuration in parsed.configurations
        )
        if expected == actual:
            result.add(Capability.CONFIGURATIONS)
    expected_parameters = tuple(
        (
            item.object_id,
            dimension.name,
            round(dimension.value_mm, 10),
            dimension.role,
        )
        for item in authored
        for dimension in item.dimensions
        if any(
            parameter.name == dimension.name and parameter.owner_id == item.source_id
            for parameter in document.parameters
        )
    )
    actual_parameters = tuple(
        (
            feature.object_id,
            dimension.name,
            round(dimension.value_mm, 10),
            (
                ParameterRole.DRIVEN
                if dimension.native_role == "display"
                else ParameterRole.DRIVING
            ),
        )
        for feature in parsed.features
        if any(item.object_id == feature.object_id for item in authored)
        for dimension in feature.dimensions
        if any(
            parameter.name == dimension.name
            and parameter.owner_id
            == next(
                item.source_id
                for item in authored
                if item.object_id == feature.object_id
            )
            for parameter in document.parameters
        )
    )
    encodable = tuple(
        parameter
        for parameter in document.parameters
        if _parameter_dimension(parameter) is not None and parameter.expression is None
    )
    if (
        len(encodable) == len(document.parameters)
        and len(expected_parameters) == len(document.parameters)
        and expected_parameters == actual_parameters
    ):
        result.add(Capability.PARAMETERS)
    expected_planes = tuple(
        (
            object_ids[f"plane:{plane.id}"],
            plane.name,
            (
                plane.transform.origin.x,
                plane.transform.origin.y,
                plane.transform.origin.z,
            ),
            (
                plane.transform.x_axis.x,
                plane.transform.x_axis.y,
                plane.transform.x_axis.z,
            ),
            (
                plane.transform.y_axis.x,
                plane.transform.y_axis.y,
                plane.transform.y_axis.z,
            ),
            (
                plane.transform.z_axis.x,
                plane.transform.z_axis.y,
                plane.transform.z_axis.z,
            ),
        )
        for plane in document.support_planes
    )
    actual_planes = tuple(
        (
            plane.object_id,
            next(
                source.name
                for source in document.support_planes
                if object_ids[f"plane:{source.id}"] == plane.object_id
            ),
            plane.origin_mm,
            plane.u_axis,
            plane.v_axis,
            plane.normal,
        )
        for plane in parsed.planes
        if any(
            object_ids[f"plane:{source.id}"] == plane.object_id
            for source in document.support_planes
        )
    )
    if expected_planes == actual_planes:
        result.add(Capability.SUPPORT_PLANES)
    return frozenset(result)


def decode_native_model(keywords: bytes, resolved: bytes) -> NativeModel:
    configurations, xml_features = _parse_keywords(keywords)
    names = _parse_names(resolved)
    classes = _parse_classes(resolved)
    scalars = _parse_scalars(resolved, names)
    record_by_id = _feature_records(xml_features, names)
    ordered_records = sorted(
        {record.offset: record for record in record_by_id.values()}.values(),
        key=lambda record: record.offset,
    )
    ends = {
        record.offset: (
            ordered_records[index + 1].offset
            if index + 1 < len(ordered_records)
            else len(resolved)
        )
        for index, record in enumerate(ordered_records)
    }
    scalar_owner = _scalar_owners(scalars, ordered_records, ends)
    native_features: list[NativeFeature] = []
    for feature in xml_features:
        record = record_by_id.get(feature.object_id)
        name = feature.name or (record.name if record is not None else "")
        if not name:
            name = f"{feature.kind or feature.xml_tag} {feature.object_id}"
        owned = scalar_owner.get(feature.object_id, ())
        dimensions = _semantic_dimensions(
            feature.kind,
            tuple(_bind_dimension(item, owned) for item in feature.dimensions),
        )
        native_end = ends.get(record.offset) if record is not None else None
        native_features.append(
            NativeFeature(
                object_id=feature.object_id,
                name=name,
                kind=feature.kind,
                xml_tag=feature.xml_tag,
                native_offset=record.offset if record else None,
                native_end=native_end,
                properties=dict(feature.properties),
                dimensions=dimensions,
                data=(
                    resolved[record.offset : native_end]
                    if record is not None and native_end is not None
                    else b""
                ),
            )
        )
    planes = _decode_planes(resolved, native_features)
    plane_by_id = {plane.object_id: plane for plane in planes}
    principal_plane_frames = _principal_plane_frames(native_features)
    principal_plane_ids = frozenset(principal_plane_frames)
    author = sorted(
        (
            feature
            for feature in native_features
            if feature.native_offset is not None
            and not _is_origin_feature(feature)
            and feature.object_id not in principal_plane_ids
        ),
        key=lambda feature: feature.native_offset or 0,
    )
    sketches: list[NativeSketch] = []
    operations: list[NativeOperation] = []
    native_index_by_id = {
        feature.object_id: index for index, feature in enumerate(native_features)
    }
    latest_sketch: NativeSketch | None = None
    latest_operation: NativeOperation | None = None
    latest_plane_id = next(iter(principal_plane_frames), next(iter(plane_by_id), 0))
    for feature in author:
        if _is_plane_feature(feature):
            latest_plane_id = feature.object_id
            continue
        if feature.kind.casefold() == "sketch":
            support = _support_plane_id(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
                latest_plane_id,
                plane_by_id,
            )
            latest_sketch = _decode_sketch(resolved, feature, support)
            native_index = native_index_by_id[feature.object_id]
            native_features[native_index] = replace(
                native_features[native_index], dimensions=latest_sketch.dimensions
            )
            sketches.append(latest_sketch)
            continue
        if feature.kind.casefold() == "extrusion":
            record = record_by_id.get(feature.object_id)
            if record is None:
                continue
            child = _integer_property(feature.properties.get("DissectableChildren"))
            profile_id = child or (latest_sketch.object_id if latest_sketch else None)
            dependencies = tuple(
                value
                for value in (
                    latest_operation.object_id if latest_operation else None,
                    profile_id,
                )
                if value is not None
            )
            family, operation_code, schema = _operation_fields(resolved, record)
            end_spec = _end_spec(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind=(
                    "join"
                    if operation_code == 0
                    else "cut" if operation_code == 2 else "native"
                ),
                profile_id=profile_id,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=_operation_dimension(feature.dimensions, "length"),
                radius_mm=None,
                family_code=family,
                operation_code=operation_code,
                schema_code=schema,
                direction_code=end_spec.direction_code if end_spec else None,
                termination_code=end_spec.termination_code if end_spec else None,
                selection_offsets=(),
                selected_local_ids=(),
            )
            operations.append(operation)
            latest_operation = operation
            continue
        if feature.kind.casefold() == "fillet":
            selections = _edge_selections(
                resolved,
                feature.native_offset or 0,
                feature.native_end or len(resolved),
            )
            selections = tuple(
                selection
                for selection in selections
                if selection[1] != feature.object_id
            )
            producer_ids = tuple(
                dict.fromkeys(selection[1] for selection in selections)
            )
            dependencies = producer_ids or (
                (latest_operation.object_id,) if latest_operation else ()
            )
            operation = NativeOperation(
                object_id=feature.object_id,
                name=feature.name,
                kind="fillet",
                profile_id=None,
                dependencies=dependencies,
                native_offset=feature.native_offset or 0,
                native_end=feature.native_end or len(resolved),
                length_mm=None,
                radius_mm=_operation_dimension(feature.dimensions, "radius"),
                family_code=None,
                operation_code=None,
                schema_code=None,
                direction_code=None,
                termination_code=None,
                selection_offsets=tuple(selection[0] for selection in selections),
                selected_local_ids=tuple(
                    dict.fromkeys(selection[2] for selection in selections)
                ),
            )
            operations.append(operation)
            latest_operation = operation
    diagnostics = []
    unresolved = [
        feature
        for feature in native_features
        if feature.native_offset is None
        and feature.object_id > 0
        and feature.object_id not in _KEYWORD_ONLY_OBJECT_IDS
    ]
    if unresolved:
        diagnostics.append(
            "native name records unavailable for "
            + ", ".join(f"{feature.object_id}:{feature.name}" for feature in unresolved)
        )
    return NativeModel(
        configurations=configurations,
        features=tuple(
            sorted(
                native_features,
                key=_native_feature_sort_key,
            )
        ),
        planes=tuple(planes),
        sketches=tuple(sketches),
        operations=tuple(operations),
        names=names,
        classes=classes,
        scalars=scalars,
        diagnostics=tuple(diagnostics),
    )


def _native_feature_sort_key(feature: NativeFeature) -> tuple[int, int]:
    if feature.native_offset is not None and feature.object_id <= 25:
        return 0, feature.native_offset
    if feature.object_id in _KEYWORD_ONLY_OBJECT_IDS:
        return 1, feature.object_id
    if feature.native_offset is not None:
        return 2, feature.native_offset
    return 3, feature.object_id


def _parse_keywords(
    data: bytes,
) -> tuple[tuple[NativeConfiguration, ...], list[_XmlFeature]]:
    root = _parse_xml(data)
    configurations: list[NativeConfiguration] = []
    features: list[_XmlFeature] = []
    for element in root.iter():
        tag = element.tag.rsplit("}", 1)[-1]
        if tag == "Configuration":
            configurations.append(
                NativeConfiguration(
                    object_id=int(element.attrib.get("id", "0")),
                    name=element.attrib.get("Name", "Default"),
                    configuration_id=int(element.attrib.get("id", "0")),
                    properties=dict(element.attrib),
                )
            )
            continue
        if element is root or tag == "Dimension":
            continue
        raw_id = element.attrib.get("id")
        if not raw_id:
            continue
        try:
            object_id = int(raw_id)
        except ValueError:
            continue
        kind = tag if tag != "Feature" else element.attrib.get("Type", "Feature")
        if kind.casefold() in PLANE_FEATURE_TYPES:
            kind = CANONICAL_PLANE_FEATURE_TYPE.title()
        name = element.attrib.get("Name", "")
        dimensions = [
            _parse_dimension(child.attrib.get("Name", ""), child.text or "")
            for child in element
            if child.tag.rsplit("}", 1)[-1] == "Dimension"
        ]
        features.append(
            _XmlFeature(
                object_id=object_id,
                name=name,
                kind=kind,
                xml_tag=tag,
                properties=dict(element.attrib),
                dimensions=dimensions,
            )
        )
    if not features:
        raise SldprtFormatError("keyword history does not contain feature nodes")
    if not configurations:
        configurations.append(NativeConfiguration(0, "Default", 0, {}))
    return tuple(configurations), features


def _parse_xml(data: bytes) -> ET.Element:
    start = data.find(b"<?xml")
    if start < 0:
        start = data.find(b"<")
    if start < 0:
        raise SldprtFormatError("XML stream contains no document element")
    try:
        return ET.fromstring(data[start:])
    except ET.ParseError as exc:
        raise SldprtFormatError(f"invalid XML metadata stream: {exc}") from exc


def _parse_dimension(name: str, text: str) -> NativeDimension:
    match = _NUMBER.search(text)
    if match is None:
        raise SldprtFormatError(f"dimension {name!r} has no numeric value")
    kind = (
        "diameter"
        if "<MOD-DIAM>" in text
        else "radius" if text.lstrip().startswith("R") else "length"
    )
    return NativeDimension(name, float(match.group()), kind, text)


def _name_marker(data: bytes) -> bytes:
    for offset in _find_all(data, CLASS_MARKER):
        if offset + 6 > len(data):
            continue
        length = struct.unpack_from("<H", data, offset + 4)[0]
        end = offset + 6 + length
        if not 1 <= length <= 128 or end + 5 > len(data):
            continue
        class_name = data[offset + 6 : end]
        if not all(0x21 <= byte <= 0x7E for byte in class_name):
            continue
        token = struct.unpack_from("<H", data, end)[0]
        if (
            token & 0x8000
            and token != 0xFFFF
            and data[end + 2 : end + 5] == b"\xff\xfe\xff"
        ):
            return struct.pack("<H", token) + b"\xff\xfe\xff"
    return bytes.fromhex("0480fffeff")


def _parse_names(data: bytes) -> tuple[NativeName, ...]:
    marker = _name_marker(data)
    names: list[NativeName] = []
    for offset in _find_all(data, marker):
        if offset + len(marker) + 1 > len(data):
            continue
        units = data[offset + len(marker)]
        text_start = offset + len(marker) + 1
        text_end = text_start + units * 2
        if not 1 <= units <= 128 or text_end + 12 > len(data):
            continue
        try:
            name = data[text_start:text_end].decode("utf-16le")
        except UnicodeDecodeError:
            continue
        if not name or any(not character.isprintable() for character in name):
            continue
        raw_id = struct.unpack_from("<I", data, text_end + 8)[0]
        names.append(
            NativeName(
                offset=offset,
                text_end=text_end,
                name=name,
                object_id=None if raw_id == 0xFFFFFFFF else raw_id,
                class_token=struct.unpack_from("<H", marker)[0],
            )
        )
    return tuple(names)


def _parse_classes(data: bytes) -> tuple[NativeClass, ...]:
    classes: list[NativeClass] = []
    for offset in _find_all(data, CLASS_MARKER):
        if offset + 6 > len(data):
            continue
        length = struct.unpack_from("<H", data, offset + 4)[0]
        end = offset + 6 + length
        if not 1 <= length <= 128 or end > len(data):
            continue
        value = data[offset + 6 : end]
        if not all(chr(byte).isalnum() or byte in b"_-" for byte in value):
            continue
        classes.append(NativeClass(offset, value.decode("ascii")))
    return tuple(classes)


def _parse_scalars(
    data: bytes, names: tuple[NativeName, ...]
) -> tuple[NativeScalar, ...]:
    scalars: list[NativeScalar] = []
    for name in names:
        value_offset = dimension_scalar_value_offset(
            data,
            name.text_end,
            len(data),
            trailing_bytes=7,
        )
        if value_offset is None:
            continue
        value = struct.unpack_from("<d", data, value_offset)[0]
        if not math.isfinite(value):
            continue
        trailer = value_offset + 8
        raw_id = struct.unpack_from("<I", data, trailer + 3)[0]
        role, operands = _scalar_trailer(data, trailer)
        scalars.append(
            NativeScalar(
                name=name.name,
                name_offset=name.offset,
                value_offset=value_offset,
                value=value,
                object_id=None if raw_id == 0xFFFFFFFF else raw_id,
                role=role,
                operands=operands,
            )
        )
    return tuple(scalars)


def _scalar_trailer(data: bytes, trailer: int) -> tuple[str, tuple[NativeOperand, ...]]:
    fixed = (
        data[trailer : trailer + 3] == b"\0\0\0"
        and data[trailer + 7 : trailer + 21] == b"\0" * 14
        and data[trailer + 24 : trailer + 29] == b"\0\0\0\x02\0"
    )
    compact = (
        data[trailer : trailer + 3] == b"\0\0\0"
        and data[trailer + 7 : trailer + 21] == b"\0" * 14
        and data[trailer + 21 : trailer + 27] == b"\x01\0\0\0\x02\0"
        and data[trailer + 28 : trailer + 35] == b"\0" * 7
    )
    legacy = (
        data[trailer : trailer + 3] == b"\0\0\0"
        and data[trailer + 7 : trailer + 24] == b"\0" * 17
        and data[trailer + 24 : trailer + 30] == b"\x0f\0\0\0\x02\0"
    )
    if compact:
        role_offset, cells, size = trailer + 27, (trailer + 35, trailer + 43), 8
    elif fixed:
        role_offset, cells, size = trailer + 29, (trailer + 35, trailer + 47), 12
    elif legacy:
        role_offset, cells, size = trailer + 30, (trailer + 36, trailer + 48), 12
    else:
        return "native", ()
    role_byte = data[role_offset] if role_offset < len(data) else 255
    role = "driving" if role_byte == 0 else "display" if role_byte == 1 else "native"
    operands: list[NativeOperand] = []
    for offset in cells:
        cell = data[offset : offset + size]
        if len(cell) != size or cell[4:8] != b"\xff" * 4:
            continue
        if size == 12 and cell[8:12] != b"\0" * 4:
            continue
        kind = struct.unpack_from("<H", cell)[0]
        if kind in {0, 0xFFFF}:
            continue
        operands.append(
            NativeOperand(offset, kind, struct.unpack_from("<H", cell, 2)[0])
        )
    return role, tuple(operands)


def _scalar_owners(
    scalars: tuple[NativeScalar, ...],
    records: list[NativeName],
    ends: dict[int, int],
) -> dict[int, tuple[NativeScalar, ...]]:
    result: dict[int, list[NativeScalar]] = {}
    for record in records:
        if record.object_id is None:
            continue
        end = ends[record.offset]
        result[record.object_id] = [
            scalar for scalar in scalars if record.offset < scalar.value_offset < end
        ]
    return {key: tuple(value) for key, value in result.items()}


def _bind_dimension(
    dimension: NativeDimension, scalars: tuple[NativeScalar, ...]
) -> NativeDimension:
    target = dimension.value_mm / 1000.0
    value_matches = [
        scalar
        for scalar in scalars
        if math.isclose(scalar.value, target, rel_tol=1e-9, abs_tol=1e-12)
    ]
    named_matches = [
        scalar for scalar in value_matches if scalar.name == dimension.name
    ]
    matches = named_matches
    if not matches and len(value_matches) == 1:
        matches = value_matches
    if not matches:
        return dimension
    scalar = next(
        (candidate for candidate in matches if candidate.role == "driving"), matches[-1]
    )
    return NativeDimension(
        name=dimension.name,
        value_mm=dimension.value_mm,
        kind=dimension.kind,
        source_text=dimension.source_text,
        native_value=scalar.value,
        native_offset=scalar.value_offset,
        native_role=scalar.role,
        operands=scalar.operands,
    )


def _feature_records(
    features: list[_XmlFeature], names: tuple[NativeName, ...]
) -> dict[int, NativeName]:
    records: dict[int, list[NativeName]] = {}
    for record in names:
        if record.object_id is not None:
            records.setdefault(record.object_id, []).append(record)
    result: dict[int, NativeName] = {}
    for feature in features:
        candidates = records.get(feature.object_id, ())
        if not candidates:
            continue
        exact = tuple(record for record in candidates if record.name == feature.name)
        selected = min(exact or tuple(candidates), key=lambda record: record.offset)
        result[feature.object_id] = selected
    return result


def _semantic_dimensions(
    feature_kind: str, dimensions: tuple[NativeDimension, ...]
) -> tuple[NativeDimension, ...]:
    semantic = {
        "extrusion": "length",
        "fillet": "radius",
    }.get(feature_kind.casefold())
    if semantic is None or not dimensions:
        return dimensions
    selected = _primary_dimension(dimensions)
    return tuple(
        replace(dimension, kind=semantic) if index == selected else dimension
        for index, dimension in enumerate(dimensions)
    )


def _primary_dimension(dimensions: tuple[NativeDimension, ...]) -> int:
    return min(
        range(len(dimensions)),
        key=lambda index: (
            dimensions[index].native_role == "display",
            dimensions[index].native_offset is None,
            (
                dimensions[index].native_offset
                if dimensions[index].native_offset is not None
                else index
            ),
            index,
        ),
    )


def _decode_planes(data: bytes, features: list[NativeFeature]) -> list[NativePlane]:
    principal = _principal_plane_frames(features)
    planes: list[NativePlane] = []
    for feature in features:
        if feature.object_id in principal:
            origin, normal, u_axis = principal[feature.object_id]
            planes.append(
                NativePlane(
                    feature.object_id,
                    feature.name,
                    origin,
                    normal,
                    u_axis,
                    _cross(normal, u_axis),
                    feature.native_offset,
                    None,
                    True,
                )
            )
            continue
        if not _is_plane_feature(feature):
            continue
        start = feature.native_offset or 0
        end = feature.native_end or len(data)
        frame = _matrix_frame(data, start, end) or _minimal_frame(data, start, end)
        if frame is None:
            continue
        offset, length, origin, normal, u_axis, v_axis = frame
        planes.append(
            NativePlane(
                feature.object_id,
                feature.name,
                origin,
                normal,
                u_axis,
                v_axis,
                offset,
                length,
            )
        )
    return planes


def _principal_plane_frames(
    features: list[NativeFeature],
) -> dict[
    int,
    tuple[
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ],
]:
    ordered = tuple(
        feature
        for _, feature in sorted(
            enumerate(features),
            key=lambda item: (
                item[1].native_offset is None,
                (
                    item[1].native_offset
                    if item[1].native_offset is not None
                    else item[0]
                ),
                item[0],
            ),
        )
    )
    origin_index = next(
        (index for index, feature in enumerate(ordered) if _is_origin_feature(feature)),
        None,
    )
    if origin_index is None:
        return {}
    planes = tuple(
        feature for feature in ordered[:origin_index] if _is_plane_feature(feature)
    )
    frames = (
        ((0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (0.0, 1.0, 0.0), (1.0, 0.0, 0.0)),
        ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    )
    return {feature.object_id: frame for feature, frame in zip(planes[:3], frames)}


def _is_origin_feature(feature: NativeFeature) -> bool:
    return feature.properties.get("Type", "").casefold() == "origin"


def _is_plane_feature(feature: NativeFeature) -> bool:
    return feature.kind.casefold() in PLANE_FEATURE_TYPES


def _matrix_frame(data: bytes, start: int, end: int) -> (
    tuple[
        int,
        int,
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    for offset in range(start, max(start, end - 121 + 1)):
        if data[offset + 48] != 1:
            continue
        origin = struct.unpack_from("<3d", data, offset)
        normal = struct.unpack_from("<3d", data, offset + 24)
        rows = (
            struct.unpack_from("<3d", data, offset + 49),
            struct.unpack_from("<3d", data, offset + 73),
            struct.unpack_from("<3d", data, offset + 97),
        )
        u_axis = tuple(row[0] for row in rows)
        v_axis = tuple(row[1] for row in rows)
        matrix_normal = tuple(row[2] for row in rows)
        values = origin + normal + u_axis + v_axis + matrix_normal
        if not all(math.isfinite(value) and abs(value) <= 10.0 for value in values):
            continue
        if not all(
            math.isclose(_norm(vector), 1.0, abs_tol=1e-9)
            for vector in (normal, u_axis, v_axis, matrix_normal)
        ):
            continue
        if any(
            abs(_dot(left, right)) > 1e-9
            for left, right in (
                (u_axis, v_axis),
                (u_axis, matrix_normal),
                (v_axis, matrix_normal),
            )
        ):
            continue
        if _dot(normal, matrix_normal) < 1.0 - 1e-9:
            continue
        return (
            offset,
            121,
            tuple(_clean(value * 1000.0) for value in origin),
            tuple(_clean(value) for value in normal),
            tuple(_clean(value) for value in u_axis),
            tuple(_clean(value) for value in v_axis),
        )
    return None


def _minimal_frame(data: bytes, start: int, end: int) -> (
    tuple[
        int,
        int,
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
        tuple[float, float, float],
    ]
    | None
):
    for offset in range(start, max(start, end - 81 + 1)):
        origin = struct.unpack_from("<3d", data, offset)
        normal = struct.unpack_from("<3d", data, offset + 24)
        if normal != (0.0, 0.0, 1.0):
            continue
        if data[offset + 48 : offset + 56] != b"\0" * 8 or data[offset + 56] not in {
            0x00,
            0x80,
        }:
            continue
        tail = struct.unpack_from("<3d", data, offset + 57)
        if tail[0] != 0.0:
            continue
        if (
            struct.pack("<d", tail[1]) != struct.pack("<d", -origin[2])
            or tail[2] != 1.0
        ):
            continue
        return (
            offset,
            81,
            tuple(_clean(value * 1000.0) for value in origin),
            normal,
            (1.0, 0.0, 0.0),
            (0.0, 1.0, 0.0),
        )
    return None


def _support_plane_id(
    data: bytes,
    start: int,
    end: int,
    fallback: int,
    planes: dict[int, NativePlane],
) -> int:
    sources = _component_plane_sources(data, start, end)
    known = [source for source in sources if source in planes]
    return known[-1] if known else fallback


def _component_plane_sources(data: bytes, start: int, end: int) -> list[int]:
    sources: list[int] = []
    for offset in range(start, max(start, end - 67 + 1) + 1):
        block = data[offset : offset + 67]
        identity = struct.unpack_from("<I", block)[0]
        legacy = struct.unpack_from("<H", block, 10)[0]
        trailer = block[47:63]
        common = (
            block[12:39] == b"\0" * 27
            and struct.unpack_from("<d", block, 39)[0] == 1.0
            and trailer[:3] == b"\0" * 3
            and trailer[3] in {2, 3, 4}
            and trailer[4:7] == b"\0" * 3
            and trailer[7] in {0xF9, 0xFB, 0xFF}
            and trailer[8:11] == b"\xff" * 3
            and trailer[11:15] == b"\0" * 4
        )
        if not common:
            continue
        if identity and block[4:10] == b"\0" * 6 and legacy:
            sources.append(legacy)
        elif identity and block[8:12] == b"\0\0\x03\0":
            sources.append(identity)
    for offset in range(start, max(start, end - 138 + 1) + 1):
        block = data[offset : offset + 138]
        source = struct.unpack_from("<I", block)[0]
        if not source or block[8:14] != b"\0" * 6 or block[14] != 1:
            continue
        if block[122:126] != struct.pack("<I", 4) or block[126:130] != b"\xff" * 4:
            continue
        basis = [
            struct.unpack_from("<3d", block, 15 + index * 24) for index in range(3)
        ]
        if not all(math.isclose(_norm(vector), 1.0, abs_tol=1e-9) for vector in basis):
            continue
        sources.append(source)
    return list(dict.fromkeys(sources))


def _decode_sketch(
    data: bytes, feature: NativeFeature, support_plane_id: int
) -> NativeSketch:
    start = feature.native_offset or 0
    end = feature.native_end or len(data)
    markers = list(_parse_markers(data, start, end))
    profiles, profile_markers, dimensions = _profiles(markers, feature.dimensions)
    normalized_markers = tuple(
        NativeMarker(
            offset=marker.offset,
            length=marker.length,
            prefix=marker.prefix,
            native_kind=marker.native_kind,
            locus=marker.locus,
            profile_role=marker.profile_role,
            state=marker.state,
            object_index=marker.object_index,
            local_id=marker.local_id,
            coordinates_mm=marker.coordinates_mm,
            endpoint_indices=marker.endpoint_indices,
            construction=(
                marker.construction
                or marker.offset not in profile_markers
                and marker.semantic != "native"
            ),
            semantic=marker.semantic,
            data=marker.data,
        )
        for marker in markers
    )
    constraints = _constraints(feature, normalized_markers, profiles)
    return NativeSketch(
        object_id=feature.object_id,
        name=feature.name,
        support_plane_id=support_plane_id,
        native_offset=start,
        native_end=end,
        markers=normalized_markers,
        profiles=profiles,
        dimensions=dimensions,
        constraints=constraints,
    )


def _parse_markers(data: bytes, start: int, end: int) -> tuple[NativeMarker, ...]:
    offsets = sorted(
        {
            offset
            for prefix in _MARKERS
            for offset in _find_all(data, prefix, start, end)
            if offset + 56 <= end
        }
    )
    markers: list[NativeMarker] = []
    for index, offset in enumerate(offsets):
        prefix_bytes = next(
            prefix for prefix in _MARKERS if data.startswith(prefix, offset)
        )
        native_offset = 17
        locus_offset = 23
        role_offset = 27
        if offset + native_offset + 4 > end:
            continue
        native_kind = struct.unpack_from("<I", data, offset + native_offset)[0]
        locus = data[offset + locus_offset : offset + locus_offset + 4]
        profile_role = struct.unpack_from("<H", data, offset + role_offset)[0]
        next_offset = offsets[index + 1] if index + 1 < len(offsets) else end
        length = next_offset - offset
        state_offset = offset + 48
        state = (
            struct.unpack_from("<d", data, state_offset)[0]
            if state_offset + 8 <= end
            else None
        )
        if state is not None and not math.isfinite(state):
            state = None
        coordinates = _marker_coordinates(data, offset, end)
        endpoints = None
        if coordinates is None:
            pair_offset = offset + 64
            if pair_offset + 4 <= end:
                pair = struct.unpack_from("<HH", data, pair_offset)
                if pair != (0, 0):
                    endpoints = pair
        object_index = (
            struct.unpack_from("<I", data, offset - 4)[0] if offset >= 4 else 0xFFFFFFFF
        )
        if object_index == 0xFFFFFFFF:
            object_index = None
        local_id = _marker_local_id(data, offset, length)
        semantic = _marker_semantic(
            native_kind, locus, coordinates, endpoints, profile_role
        )
        markers.append(
            NativeMarker(
                offset=offset,
                length=length,
                prefix=prefix_bytes.hex(),
                native_kind=native_kind,
                locus=locus.hex(),
                profile_role=profile_role,
                state=state,
                object_index=object_index,
                local_id=local_id,
                coordinates_mm=coordinates,
                endpoint_indices=endpoints,
                construction=profile_role == 2,
                semantic=semantic,
                data=bytes(data[offset:next_offset]),
            )
        )
    return tuple(markers)


def _marker_coordinates(
    data: bytes, offset: int, end: int
) -> tuple[float, float] | None:
    for relative in (56, 64):
        coordinate_offset = offset + relative
        if data[coordinate_offset : coordinate_offset + 2] != _COORDINATE_TAG:
            continue
        if coordinate_offset + 18 > end:
            continue
        x, y = struct.unpack_from("<2d", data, coordinate_offset + 2)
        if (
            math.isfinite(x)
            and math.isfinite(y)
            and abs(x) <= 1000.0
            and abs(y) <= 1000.0
        ):
            return _clean(round(x * 1000.0, 12)), _clean(round(y * 1000.0, 12))
    return None


def _marker_local_id(data: bytes, offset: int, length: int) -> int | None:
    relative = MARKER_LOCAL_ID_OFFSET_BY_LENGTH.get(length)
    if relative is None or offset + relative + 4 > len(data):
        return None
    value = struct.unpack_from("<I", data, offset + relative)[0]
    return None if value == 0xFFFFFFFF else value


def _marker_semantic(
    native_kind: int,
    locus: bytes,
    coordinates: tuple[float, float] | None,
    endpoints: tuple[int, int] | None,
    profile_role: int,
) -> str:
    if profile_role == 2:
        if native_kind == 2 and endpoints is not None and endpoints[0] != endpoints[1]:
            return "line"
        return "native"
    if locus == _CIRCLE_LOCUS and coordinates is not None:
        return "circle"
    if locus == _POINT_LOCUS:
        if coordinates is not None:
            return "point"
        if endpoints is not None and endpoints[0] != endpoints[1]:
            return "line"
        return "reference"
    return "native"


def _linked_rectangle_profiles(
    markers: list[NativeMarker],
) -> tuple[tuple[NativeProfile, ...], set[int]]:
    profiles: list[NativeProfile] = []
    used: set[int] = set()
    for start in range(max(0, len(markers) - 8)):
        records = markers[start : start + 9]
        if len(records) != 9 or any(marker.offset in used for marker in records):
            continue
        points = records[:4]
        header = records[4]
        lines = records[5:]
        prefix = points[0].prefix
        locus = points[0].locus
        if (
            locus != _CIRCLE_LOCUS.hex()
            or any(
                marker.prefix != prefix
                or marker.locus != locus
                or marker.profile_role != 1
                or marker.native_kind != 0
                or marker.coordinates_mm is None
                for marker in points
            )
            or header.prefix != prefix
            or header.locus != locus
            or header.profile_role != 1
            or header.native_kind != 0
            or header.coordinates_mm is not None
            or header.endpoint_indices is None
            or header.length != 92
            or any(
                marker.prefix != prefix
                or marker.locus != locus
                or marker.profile_role != 1
                or marker.native_kind != 1
                or marker.coordinates_mm is not None
                or marker.endpoint_indices is None
                for marker in lines
            )
            or any(marker.length != 92 for marker in lines[:-1])
            or lines[-1].length < 92
        ):
            continue
        coordinates = tuple(marker.coordinates_mm for marker in points)
        if any(coordinate is None for coordinate in coordinates):
            continue
        resolved = tuple(
            coordinate for coordinate in coordinates if coordinate is not None
        )
        xs = sorted({coordinate[0] for coordinate in resolved})
        ys = sorted({coordinate[1] for coordinate in resolved})
        if len(xs) != 2 or len(ys) != 2 or len(set(resolved)) != 4:
            continue
        corners = {(x, y) for x in xs for y in ys}
        if set(resolved) != corners:
            continue
        header_start, header_end = header.endpoint_indices
        if (
            header_start >= len(resolved)
            or header_end >= len(resolved)
            or header_start == header_end
        ):
            continue
        diagonal_start = resolved[header_start]
        diagonal_end = resolved[header_end]
        if math.isclose(
            diagonal_start[0], diagonal_end[0], abs_tol=1e-9
        ) or math.isclose(diagonal_start[1], diagonal_end[1], abs_tol=1e-9):
            continue
        edge_markers: dict[str, NativeMarker] = {}
        valid = True
        for marker in lines:
            endpoint_start, endpoint_end = marker.endpoint_indices or (-1, -1)
            if (
                endpoint_start < 0
                or endpoint_end < 0
                or endpoint_start >= len(resolved)
                or endpoint_end >= len(resolved)
                or endpoint_start == endpoint_end
            ):
                valid = False
                break
            point_start = resolved[endpoint_start]
            point_end = resolved[endpoint_end]
            if math.isclose(point_start[1], point_end[1], abs_tol=1e-9):
                side = (
                    "bottom"
                    if math.isclose(point_start[1], ys[0], abs_tol=1e-9)
                    else "top"
                )
            elif math.isclose(point_start[0], point_end[0], abs_tol=1e-9):
                side = (
                    "left"
                    if math.isclose(point_start[0], xs[0], abs_tol=1e-9)
                    else "right"
                )
            else:
                valid = False
                break
            if side in edge_markers:
                valid = False
                break
            edge_markers[side] = marker
        if not valid or set(edge_markers) != {"bottom", "right", "top", "left"}:
            continue
        edge_offsets = tuple(
            edge_markers[side].offset for side in ("bottom", "right", "top", "left")
        )
        metadata_offsets = tuple(
            marker.offset
            for marker in (*points, header)
            if marker.offset not in edge_offsets
        )
        consumed = {marker.offset for marker in records}
        profiles.append(
            NativeProfile(
                "rectangle",
                (xs[0], ys[0], xs[1], ys[1]),
                (*edge_offsets, *metadata_offsets),
            )
        )
        used.update(consumed)
    return tuple(profiles), used


def _profiles(
    markers: list[NativeMarker], dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], set[int], tuple[NativeDimension, ...]]:
    linked_rectangles, linked_markers = _linked_rectangle_profiles(markers)
    remaining_markers = [
        marker for marker in markers if marker.offset not in linked_markers
    ]
    circle_profiles, circle_dimensions = _circle_profiles(remaining_markers, dimensions)
    normalized = tuple(
        (
            replace(dimension, kind=circle_dimensions[index])
            if index in circle_dimensions
            else dimension
        )
        for index, dimension in enumerate(dimensions)
    )
    points = [
        marker
        for marker in remaining_markers
        if marker.coordinates_mm is not None and marker.locus == _POINT_LOCUS.hex()
    ]
    coordinates = list(dict.fromkeys(marker.coordinates_mm for marker in points))
    rectangles: list[tuple[float, float, float, float]] = []
    xs = sorted({point[0] for point in coordinates})
    ys = sorted({point[1] for point in coordinates})
    coordinate_set = set(coordinates)
    for x0, x1 in itertools.combinations(xs, 2):
        for y0, y1 in itertools.combinations(ys, 2):
            if {(x0, y0), (x0, y1), (x1, y0), (x1, y1)} <= coordinate_set:
                rectangles.append((x0, y0, x1, y1))
    values = [dimension.value_mm for dimension in dimensions]
    matches = [
        rectangle
        for rectangle in rectangles
        if _matches(rectangle[2] - rectangle[0], values)
        and _matches(rectangle[3] - rectangle[1], values)
    ]
    if matches:
        minimum = min(
            (rectangle[2] - rectangle[0]) * (rectangle[3] - rectangle[1])
            for rectangle in matches
        )
        selected = [
            rectangle
            for rectangle in matches
            if math.isclose(
                (rectangle[2] - rectangle[0]) * (rectangle[3] - rectangle[1]),
                minimum,
                abs_tol=1e-7,
            )
        ]
    else:
        selected = []
        for group_start in range(max(0, len(points) - 3)):
            group = points[group_start : group_start + 4]
            products = {marker.coordinates_mm for marker in group}
            gx = sorted({point[0] for point in products})
            gy = sorted({point[1] for point in products})
            if len(gx) == 2 and len(gy) == 2 and len(products) == 4:
                selected = [(gx[0], gy[0], gx[1], gy[1])]
                break
        if not selected and rectangles:
            selected = [
                max(
                    rectangles,
                    key=lambda rectangle: (rectangle[2] - rectangle[0])
                    * (rectangle[3] - rectangle[1]),
                )
            ]
    selected.sort(
        key=lambda rectangle: min(
            (
                marker.offset
                for marker in points
                if marker.coordinates_mm
                in {
                    (rectangle[0], rectangle[1]),
                    (rectangle[0], rectangle[3]),
                    (rectangle[2], rectangle[1]),
                    (rectangle[2], rectangle[3]),
                }
            ),
            default=1 << 62,
        )
    )
    line_markers = [
        marker
        for marker in remaining_markers
        if marker.semantic == "line"
        and marker.profile_role == 1
        and marker.locus == _POINT_LOCUS.hex()
    ]
    runs: list[list[NativeMarker]] = []
    for marker in line_markers:
        if not runs or marker.offset - runs[-1][-1].offset != 92:
            runs.append([marker])
        else:
            runs[-1].append(marker)
    profile_lines = [
        tuple(run[index : index + 4])
        for run in runs
        for index in range(0, len(run), 6)
        if len(run[index : index + 4]) == 4
    ]
    profiles: list[NativeProfile] = [*circle_profiles, *linked_rectangles]
    used: set[int] = linked_markers | {
        offset for profile in circle_profiles for offset in profile.marker_offsets
    }
    for index, rectangle in enumerate(selected):
        span = tuple(
            marker.offset
            for marker in (profile_lines[index] if index < len(profile_lines) else ())
        )
        if circle_profiles and len(span) != 4:
            continue
        used.update(span)
        corners = {
            (rectangle[0], rectangle[1]),
            (rectangle[0], rectangle[3]),
            (rectangle[2], rectangle[1]),
            (rectangle[2], rectangle[3]),
        }
        used.update(
            marker.offset
            for marker in markers
            if marker.semantic == "point" and marker.coordinates_mm in corners
        )
        profiles.append(NativeProfile("rectangle", rectangle, span))
    profiles.sort(key=lambda profile: min(profile.marker_offsets, default=1 << 62))
    return tuple(profiles), used, normalized


def _circle_profiles(
    markers: list[NativeMarker], dimensions: tuple[NativeDimension, ...]
) -> tuple[tuple[NativeProfile, ...], dict[int, str]]:
    centers = [
        marker
        for marker in markers
        if marker.semantic == "circle" and marker.coordinates_mm is not None
    ]
    if not centers:
        return (), {}
    candidates: dict[
        int,
        dict[
            tuple[float, float, float],
            list[tuple[NativeMarker, NativeMarker, str]],
        ],
    ] = {}
    for center in centers:
        following = next(
            (
                marker
                for marker in markers
                if marker.offset > center.offset
                and marker.coordinates_mm is not None
                and not _same_point(marker.coordinates_mm, center.coordinates_mm)
            ),
            None,
        )
        if following is None:
            continue
        radius = math.dist(center.coordinates_mm, following.coordinates_mm)
        if not math.isfinite(radius) or radius <= 1e-12:
            continue
        for index, dimension in enumerate(dimensions):
            semantic = None
            normalized_radius = radius
            if math.isclose(dimension.value_mm, radius, rel_tol=1e-7, abs_tol=1e-7):
                semantic = "radius"
                normalized_radius = dimension.value_mm
            elif math.isclose(
                dimension.value_mm, radius * 2.0, rel_tol=1e-7, abs_tol=1e-7
            ):
                semantic = "diameter"
                normalized_radius = dimension.value_mm / 2.0
            if semantic is None:
                continue
            geometry = (
                center.coordinates_mm[0],
                center.coordinates_mm[1],
                normalized_radius,
            )
            candidates.setdefault(index, {}).setdefault(geometry, []).append(
                (center, following, semantic)
            )
    result: list[NativeProfile] = []
    geometries: set[tuple[float, float, float]] = set()
    normalized: dict[int, str] = {}
    for index, dimension in enumerate(dimensions):
        matches = candidates.get(index, {})
        if len(matches) != 1:
            continue
        geometry, records = next(iter(matches.items()))
        if geometry in geometries:
            continue
        semantics = {semantic for _, _, semantic in records}
        if len(semantics) != 1:
            continue
        geometries.add(geometry)
        normalized[index] = next(iter(semantics))
        result.append(
            NativeProfile(
                "circle",
                geometry,
                tuple(
                    sorted(
                        {
                            offset
                            for center, following, _ in records
                            for offset in (center.offset, following.offset)
                        }
                    )
                ),
                dimension.name,
                normalized[index],
            )
        )
    result.sort(key=lambda profile: min(profile.marker_offsets))
    return tuple(result), normalized


def _same_point(left: tuple[float, float], right: tuple[float, float]) -> bool:
    return math.isclose(left[0], right[0], abs_tol=1e-12) and math.isclose(
        left[1], right[1], abs_tol=1e-12
    )


def _constraints(
    feature: NativeFeature,
    markers: tuple[NativeMarker, ...],
    profiles: tuple[NativeProfile, ...],
) -> tuple[NativeConstraint, ...]:
    constraints: list[NativeConstraint] = []
    radial_parameters: set[str] = set()
    for profile_index, profile in enumerate(profiles):
        if profile.kind == "rectangle":
            for edge_index in range(4):
                constraints.append(
                    NativeConstraint(
                        id=f"{feature.object_id}:profile:{profile_index}:axis:{edge_index}",
                        kind="horizontal" if edge_index % 2 == 0 else "vertical",
                        references=(
                            f"{feature.object_id}:profile:{profile_index}:edge:{edge_index}",
                        ),
                        parameter=None,
                        value=None,
                        native_offset=(
                            profile.marker_offsets[edge_index]
                            if edge_index < len(profile.marker_offsets)
                            else None
                        ),
                        native_code=None,
                    )
                )
        elif profile.kind == "circle":
            semantic = profile.dimension_kind or "radius"
            parameter_name = profile.parameter_name
            if parameter_name is not None:
                radial_parameters.add(parameter_name)
            constraints.append(
                NativeConstraint(
                    id=f"{feature.object_id}:profile:{profile_index}:{semantic}",
                    kind=semantic,
                    references=(f"{feature.object_id}:profile:{profile_index}",),
                    parameter=(
                        f"{feature.object_id}:{parameter_name}"
                        if parameter_name is not None
                        else None
                    ),
                    value=(
                        profile.coordinates[2] * 2.0
                        if semantic == "diameter"
                        else profile.coordinates[2]
                    ),
                    native_offset=(
                        profile.marker_offsets[0] if profile.marker_offsets else None
                    ),
                    native_code=None,
                )
            )
    for dimension in feature.dimensions:
        if dimension.name in radial_parameters:
            continue
        constraints.append(
            NativeConstraint(
                id=f"{feature.object_id}:dimension:{dimension.name}",
                kind="distance",
                references=tuple(
                    f"native:{operand.kind_code:04x}:{operand.entity_index}"
                    for operand in dimension.operands
                ),
                parameter=f"{feature.object_id}:{dimension.name}",
                value=dimension.value_mm,
                native_offset=dimension.native_offset,
                native_code=None,
            )
        )
    for marker in markers:
        if marker.semantic != "relation":
            continue
        constraints.append(
            NativeConstraint(
                id=f"{feature.object_id}:native-relation:{marker.offset}",
                kind=f"native_{marker.native_kind}",
                references=tuple(
                    f"native-index:{index}" for index in marker.endpoint_indices or ()
                ),
                parameter=None,
                value=None,
                native_offset=marker.offset,
                native_code=marker.native_kind,
            )
        )
    return tuple(constraints)


def _operation_fields(
    data: bytes, record: NativeName
) -> tuple[int | None, int | None, int | None]:
    if record.text_end + 12 > len(data):
        return None, None, None
    family = struct.unpack_from("<H", data, record.text_end + 4)[0]
    operation = data[record.text_end + 6]
    schema = data[record.text_end + 7]
    repeated_id = struct.unpack_from("<I", data, record.text_end + 8)[0]
    if repeated_id != record.object_id:
        return None, None, None
    return family, operation, schema


def _end_spec(data: bytes, start: int, end: int) -> NativeEndSpec | None:
    for offset in range(start, max(start, end - 26 + 1) + 1):
        prefix = data[offset : offset + 2]
        if prefix != b"_c" and not (
            len(prefix) == 2
            and struct.unpack("<H", prefix)[0] & 0x8000
            and prefix != b"\xff\xff"
        ):
            continue
        if data[offset + 2 : offset + 4] != b"\0\0":
            continue
        if struct.unpack_from("<I", data, offset + 4)[0] != 1:
            continue
        if struct.unpack_from("<I", data, offset + 8)[0] not in {0, 1}:
            continue
        direction = struct.unpack_from("<I", data, offset + 12)[0]
        if direction not in {0, 1} or data[offset + 16 : offset + 18] != b"\0\0":
            continue
        termination = struct.unpack_from("<I", data, offset + 18)[0]
        second = struct.unpack_from("<I", data, offset + 22)[0]
        if termination > 64 or second > 1:
            continue
        return NativeEndSpec(offset, termination, direction, second)
    return None


def _edge_selections(
    data: bytes, start: int, end: int
) -> tuple[tuple[int, int, int], ...]:
    selections: list[tuple[int, int, int]] = []
    for offset in _find_all(data, _EDGE_SELECTION_IDENTITY, start, end):
        if offset + 38 > end:
            continue
        producer = struct.unpack_from("<I", data, offset + 26)[0]
        local_id = struct.unpack_from("<I", data, offset + 34)[0]
        if producer and local_id:
            selections.append((offset, producer, local_id))
    return tuple(selections)


def _operation_dimension(
    dimensions: tuple[NativeDimension, ...], semantic: str
) -> float | None:
    return next(
        (dimension.value_mm for dimension in dimensions if dimension.kind == semantic),
        None,
    )


def _integer_property(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _find_all(
    data: bytes, marker: bytes, start: int = 0, end: int | None = None
) -> list[int]:
    result: list[int] = []
    cursor = start
    limit = len(data) if end is None else end
    while True:
        offset = data.find(marker, cursor, limit)
        if offset < 0:
            return result
        result.append(offset)
        cursor = offset + 1


def _matches(value: float, candidates: list[float]) -> bool:
    return any(math.isclose(value, candidate, abs_tol=1e-6) for candidate in candidates)


def _norm(vector: tuple[float, float, float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def _dot(left: tuple[float, float, float], right: tuple[float, float, float]) -> float:
    return sum(a * b for a, b in zip(left, right, strict=True))


def _cross(
    left: tuple[float, float, float], right: tuple[float, float, float]
) -> tuple[float, float, float]:
    return (
        left[1] * right[2] - left[2] * right[1],
        left[2] * right[0] - left[0] * right[2],
        left[0] * right[1] - left[1] * right[0],
    )


def _clean(value: float) -> float:
    return 0.0 if abs(value) <= 1e-12 else value
