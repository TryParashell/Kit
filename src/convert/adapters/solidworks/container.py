# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

import base64
from dataclasses import dataclass
from pathlib import Path
import struct
from types import MappingProxyType
from typing import Iterable, Mapping
import zlib

from .format import CONTENT_TYPES_STREAM, CONTAINER_VERSIONS, RELATIONSHIPS_STREAM

_LOCAL_SIGNATURE_PREFIX = bytes.fromhex("140006000800")
_LOCAL_SIGNATURE_SIZE = 10
_DEFAULT_FILE_ID = 0xEC6E2386
_DEFAULT_TYPE_ID = 0x1C34D281
_TYPE_IDS_BY_NAME = {
    "Header2": 0x1C74D22C,
    "Preview": 0x1C74D22C,
}
_SIGNATURE_ENTRY_SIZE = 16
_SIGNATURE_TABLE_ENTRIES = 1000
_SIGNATURE_TABLE_B85 = (
    "f?Wp$fL;Uwf^Go>czy^2v!>fTnLZ4M91UJ1-bc3vvl30nri;5neOdz_A0;>mUDV6`J4N-D3W*I9G"
    "OpVkAevC_{Wf?&_A*Hl+(~_&txpv4&}KkHw=l$OBB47n_9Bs;+8>MI0-4INNu6@JEP#H+fa%ql%*"
    "pDq)@Q#{zZBMfW{%t~NmuWKk7@s5Va?GVau%GO@EzuIcS=u$0@vs{$;(qLbTb|j)$|OW)SuL(&oz"
    "Eo%=98MEs)dCNYjsXDjnJ8EBC<VM2CTR4qs3JzKvnj2NeZ-AA&PG7;uu>vCdRv6=^<&1Zqb3mU9l"
    "-XlE}LN=o<Cc4$}7`WCwph$OD9+fx2{Jmo_r^hMLy^$X4@Jy~GIS&Ao@b}i7t)M(AgC3$K|6hL7J"
    "u{&y|jKL@ohYP9J@h^;*6&;$Dz~P(0nyBf1wZev{RKJ?%Rna5a(I_~OW}$4^UQXdKaoPTy;-%uBN"
    "3@#^WjHEEd4j2l!gzLi-zKqR+9_>55|-d%ra8Yf@m`5PZ4TpXAReJ81H#K4ga<)C4-^Gu$zdoPjx"
    "6WJ+z2*C^QevfaqIHFJJ6v2evAfnhj?>MzJk8cK}N#cF#3!ue{k@pl`@7@6KGqi_59`w%D#P{8$p"
    "VRXivEP6nk>^na$G;v^qraGgD@!5TVNpUQFx*1?F>1stz%<u+`74$|wKW^i33<LRlwy_`#ff&5Va"
    "2rnqDyuuPSQEl!PEndd#RfU(|S=|Kps)ulmapX3;yCICVeA<<0!voDhbk8@K%ey@r{&(&|r&Xu9l"
    "TE1l`tq1lhre(gNX~4;}GBgP+7moo=o!iD%3)rT}h=Dj^ViIU;=g?I7ct{s<4U#Dxa+xWH`W$rIw"
    "YWD=u$5Q!ZES$wi`jII2oYsNrS^HfxE1U7k6_{8^m{yRTVjfe_gp8BJ4%P;Kw+CQgvP_M5K1to18"
    ";Ti?`obe5Kx=QC@DjMp6T|ANP(e8F>KAGqk-O@{}7mr&&@-cSI1CUCmg-MU4JM8Nx5H%G)`bVm;&"
    "DAD-E(jyX+LUxG!_!9esXLAJc@`Yf!!c7S=-{7!?_VE-WjU+z$DRyzt5nF_djRjjwc))sUpMUTQ%"
    "6O9FO)u{LWLT7BCg>T(`}jHq#qPT5|#u)q4Rlyn_+SP<OhTk_gQTz{Z}%N;i9RRVNL3mUA_BPOZ$"
    "KwG0TXoxkr)hgkw3SBa?<yze7wd-AXY&ykhR}Gkx>xY`(qOxcN#-!%ejbC@X!;jV~)TtC97y%Ikb"
    "GxpM9AL^IFV<bp*C|s)4a`}n>L%?~*@S>jxHtGKpnBEqTu%C*Haz?xuz`++vF^Wp<b~-H?8b`+^P"
    "}Qs29Wf*GP(2w;4Ccy_;djtq6?5iHx`lzH?<s7at=2>%trG2CJBD_Rqfb%SIQEX2yC_jZa=W#-<u"
    "pd-9TSD8|1mVz@}jxyvXH}cS<XG3RxJ#4r&TQ55954+X2Jl8nQ6|iTGtAJq0{b{l2qG&>5bMq5f&"
    "q?Pmn~6dB3C^7uc|2xw8Q0_?@Wl<X3egZ40KuVa-#q20aXF;Ci9%Kgqb#a!=YFvMx);+(JEOE$J%"
    "z5rG)RBD8W+H7Ao%L>IjNj(Mg^4AW^kC^naPa+s}SU+?}E>uGAwmH7v9A^yX8+2U$Zfl))M5joTx"
    "B@=21c$aTR^;6xZhK+f=Uj|E#Am!O%*p@qsgM&7tsW61OF`w5^<qCLsr|0FQ86n?%7E-HH8~nZWg"
    "Nb$SG{-6v(w2JG8Rq>5QY!-ge}q&w<flt(E`|bArr6e-YHqS#-=J|Hb?Z&OWo@ssF`Y_62Raz$8I"
    "2zggsAUX{ey?3?k4ZC_fl~0n4et<h|MdWVkbnK*QOZH(>^jAcHb=46lRzF+`#x+8DE3Vc`idG<A1"
    "SV@mCs;YmIFECTsdPPPh{d7pX0fQ)c_M@`^A3SV?8SxZBjE4x}SwQSs!TAePOCzyw1nC?iZy+}wi"
    "Zr<_2Ne;uIynx5G;tRq)xz4w-WOlO=%?P7u>l`Q*=~}qIT-sH)K49t-+$EJ+@~>@xSA*r!#GvU#`"
    "VVL90y~e&x%uJbRw6CY%L6>_jj9*1DFp?tD1U;+5^C?jLg_z?im^{Iu8{Y4*6p7J5+;A_0Y&_-pK"
    "aH4T6L$IFwKyu^h<}O?r^V;B`T()3X5yl2#c`U(K1ff`*(MNR82|EAr5j$zKg$|;RHF;{XnE0Wgi"
    "MRXq8ZO9lA$-HqtbnIYjm&#Ho%fGQmKdaj)`ZK}hn@313Fm=7j&2U&R;2V>A3dtCEDnKdPe$@IM?"
    "?#7|MJURaiefgXs}R*bvp$R%x`84U^RF$YQ=0a)yp6?_fV4@jyA6wt^)qmk&dkYF!Rx8sE?FCZP`"
    "En+CsT^A5g#P{gu$l<8s&pKtw;w>y#EZkrWVmt+6`o)>B!)QP!BrUqD#G4SoVe$Of=F>{QAix3@@"
    "}=ma^6CfIaJPqH*RhA&F+}O*;T>~=#+-AFJy+Du2BEO5oi{q~j7!W0hD^5qHYFKX*Cms3r_PScC}"
    "}*u#(6`Bf))9pK5h3O*~YP-{Dz7h%yT4Aw6cSNjJ>0ATXl;&DeVoFu4V7Ccjw<ks;?qJNN(=K5|B"
    "Ez4;*r9?c8qB8YMq+1$&;#33jM;Y3Iwz(SEpe?68_~Sxyf%qxjZP-X~SyYxnDHHa&E^VRvl7@e51"
    "~XjzTC6C31MrVpyX{8<-?2Oz$prvj^;xu@+dFMV(?uGIUV<x5vv9%|Al{3TBk0zdzA1CF($n!hy`"
    "6Fu#S=W5CzcBRtBGEp^@XY#`)gPfM=^Qrq)D+exxCb5gZJ7D8VZ}Pk%3Jbjm!zVmzvwv&{9~$F4m"
    "B+t;??MrL(E%<Zclv$x&*D*zn=XQhx-e(jF00nx|3=Uf_gG10(v*|3H-&x5sT|oYbZ%WKzxHrx$s"
    "#?*lFdp$#9a9%WnlXOS6d?{zXCq(*iV)7>Kkynmq>nkb)*v%;I!&wv#v}RenZ)lI^1T~PC4<8WaU"
    "lRLFEI2(GwJv)5_$><i>FQR0ju`LGn8BUz9teRh{w3Zox8U&SEvoBL%PbAMj1OgKZPO{fnYSk;pm"
    "O<%&X+$D?(xlh|LsTFerijC9Rbus&vsmhp$$Z#}fxI`%3;^HnqCNxpb^|B2RNRGHV>g+XYEGiuMd"
    "eq3`(e<zULo1N2*7hGxno1??(pQ%z!sz8B2{6A#rNQ*$#+Gbm7XGFg<Ci)v%wSuAHl<FwA#{n8Q8"
    "n`TSR5RfsbNhAk{t{kYp5S$p)s8srT%|xDgHD<DwHy&$D!m`rb1uby3C<XkrdD3DgfCFH9wCB}hV"
    "5tt^tJl2Q;))*0!K3!FG5vaW~0EpNX@Y31E|&!d8X~{0LjjFRuhsTM~$b#88m%F2M~h3tk5ANGk_"
    "$i1VfTF0ik!byRcUSYe@-+Z*BO`vE_`sHK1!2)$&we&WgTe9);X>3(eT@mBc}D*tIW*i)zNeZKYO"
    "b5=KrwfJN8^f4t?s&D7qG?n5|+{L_f?zUCOv+efOr5ybjS!8%HwO^|w+i7YXNo)Of}gpq8TaiePY"
    "2k$Pw`?NujIx>5=ut$Ro$32;T%ys@z7_~$P&F7>#dIPH%_gx7Tll0Ts&noC45O3Zgp|+nGUkG-;`"
    "unb<yY1<2E(ko|b4t34(}9uT>ng_;L>-+f0#a;DA181*QWLOh$Nj+ig8G<M<CJGl;np1k-SXm)s9"
    "TISWwO!)$lu7c>x6%7Y0cHYD5_9-dE2OxmVH!E`szRf^X9z`q__C<!sTB*(2Lnp$_+JRJE1UZl?B"
    "~&pvmt&@(CAPZUqU?b7x9+Ui=M}@B{xBuaSK<0@P#!LB0TMiDb(5uQ0^&CsQXLyyw>u!qt?VUJ+K"
    "A1~AYDg_7MC;Xl0R?V#=f1@YcJk`|y$Y0KXF&x(aV$zltH77gviA>!9Hv%ONMHi=f;hfmSa4J^bt"
    "ie=Ewa<Tk{nf90fa+Cq+hVQqE;bVCLLtD@#)j};|7zhCGDQAlkxfe!I{GKEU@SfySFUKyoZvqF=>"
    "Qe)K0Nve57|WnB95!D&=13=>crv1>Nc>#`vkTl_bf_(m%1SPUWF#Z)Y8*>TS=#clrxUp}Q%mmewm"
    "`X5nu(L8|GB+NIJ^8yOp$X4e4K4d1F7+yc>KzOA!h|SggqU@CXrA<y4Vy|X<R+|c-DY$7F`mH;aA"
    "thn@K2_TMo1H$2zbP62eguYey2Mbk7qkXqDrrv!njL&8~{|M?yV3Y8<6wX~Ud~_ZVB3na~b|f4VK"
    "187e4uUS5;jZz7|nn4k9F=ONz4xR`!b4k1~B<u$koIWjx<_aLj&{PxW`*eh);vnBn_Q;+3m{0iJH"
    "B5X{aI|Ly|K)pI*6$YdJvnbH>_7~%)bH(;mi_?IOyveZuNa(<B;Qpu)<CzZpu>R=V*FSb$z5yGk;"
    "=?PeJ+rRZh$RAafT&$*j`{RER~3DYf8?O{+zq?uDkH{@Es_n+A_dK2$A-c2J#0V3Fx6ME6;MZdcC"
    "S5}iaR<!63vu}KF$k2USB*h7(3OT#HT&&!pT+gG_VUvD^qR6cFqj42Farn?D{vdNUosKn(_GTu9&"
    "f9z1NI=HM2=4;QT!Bpgw))8Xy?^^$dn)Ivi0{00l$ay6z~w&!e?(*}v}WG<AW(keNx9MxSwHEs+h"
    "*;aBrq(z{2JA!?YV=zr)=>$R7x^(`<4WUWZk`nUH1c-X1&t_V?sR8ic}m8A2%>`14r@}xJ|cYpJ|"
    "DfQNt?#@l2^_#93kf3PzXqMOEV04+zF2%)?rd?SkL$z@<YJ$ggP&~)k{GTKx>b_iKZ-P}8QdvR08"
    "IEKb&t8#)6+HiQXSD)P!Ik)6qJm26K)S<@1t=BZ`CR**RapKl7DV2q;myba2F%Q`7)xj%{A0{K@c"
    "O8OZVd*zT?&BMmf=bhXG?;2^oocc)q;Pk%EneIx|d=vpXzRUaNgf7y<9BBp!k+LvltYyV2xKZ(=1"
    "A049BZ#wL2N(6+7b7vi)tqHJonIYQ9);LDsloKiiSyj#2Bs*GTaE)rnJco(%I3&Hr%3Lc={~0mEw"
    "DH5?JZ=l+VbE?C>oH!=9MsL`mp5$Fb-VsWXNC%!aJ-8QuRz?SgP;<dwM!<m^s`IK|Vs34c%@(zU&"
    "J1*c|U~^%fz~P3S8l{fG0V)8yxSTsdJaCE_9OJsy#(Ole<{1F6kfySt{&6PodQ9}u4l?R3a-K=e1"
    "~@PAPYn6<mT`DF*RS1Zw_$PlwP-vkBc5lK^m03e*j3AEUQ71MnZvU}KEiNzZM<3HI^>~h9w?fCYP"
    "QJByMcH{d!O~+7gw0lZK%;yN6f{wk}B&xC>U$^doWle*99GsFL1osH*^p23n^-gZr7Z8M4;kHXtl"
    "xt(5X`zQz@ZQ0Vfq<A!7iizzm|I3MR-m*sx7E2S|se5$Yl|S2gaAdMd^r{%uqJHXGm}LIE)L*TMF"
    "#EE%Hi<+v;R4RPyGAmW$0_So?H5*&_^KCisK$U37}0C4-_^xoI?n<aptez#KFFzmpm|JW0GCwf$v"
    "Gld=6tCf3+=OT`*DVUXo84|rI)$^$eqZij<C8*$vpb0GARL=<PW=^@N;1d!Eds(7Q3^SB2rl3O6U"
    "xG-Vm@bzKBWQ~e7%0AP=ic8iEB43k{`G1Yu|2#}{!nz>qFg8nL8k2jrg;a8XF=r!u}}21(t#1uY_"
    "zRwDOycSNBgCN*3uNmw+Q-#h=dA{md^7@u^)3|e$IWR3Fo=<4s+KX2{Y<u^q&FXaqc(QVcCmR!xw"
    "kckW-Y0#zCRne=UZA0~1#11q6dBOUPB^n%aYVFR%nENefz;hpz4qB9D4k?6^NykpSrCJz7e>$vC8"
    "F9yA1TQocB2ba#f6fC73(>uZm>KwFofaO?nXcU!i@x9MK6QZtlpw&YWAAn#E2D0D3ryxscV48~pi"
    "E31JsBN+Pa@-x>#bv!(;ioC)Q%o_oAs!n()I510XZjj7ji3q?l+J<Um*vTkYN7I=+|ETlgwRL$09"
    "C5MD$8ury5(AiqvGlWG2+;v>-kO{t=wj<&gBxW5;nH>@zPSdL=1*$!A4MFzEuF3d*L#&{u#?gIya"
    "=VBubYH)+s%aREHxf{&Oi(RZgm$HyWC2+eu0g+2?U>PtrWt`rxv214gH)iW3KD9^PnWO5hsPZdvp"
    "h(64$)!1cVqcsr@Qiu<y(eiB}+E<!HU)VZ#g-&$cMNen@1f+cj>gY3Sm?K2w${<^vUvY!k|=G#IC"
    "Ip^nxR^&tQ#TWzdDa6puP-f-iAB6=~zuj(@s5RM>u8AJN7At?6staZEpMQ#Q;xsRD3=7Zdd*EQfJ"
    "fQ>%UVIF;zrzWtL^_79?ao7Qw_V}U?+US003p}~$34O>To@YhQGUAkzUlivEdgx3>zVqZ&rEh=db"
    "VjFUHO7Y)`(`|2XeJDG5j@pp>IJdsImk)+@8L*|Ih~NDi_k+;o?=N`@wk7&GgCANNS5|0j=s1DVg"
    "*0tgoj?NlLW(puccGIc41Wo@1pAV9R=jD<{lV>q@~StdQJC**2vLHS9L^{pXv3(YjNQ_@VP@IXfR"
    "WDU58r4MK?t_+l4bzy&D7P6Bx;c&j|nBNgCTNJv>n8Hgr#14U8_!Dx|VT3*UIWd$u^$M6NF6u#j_"
    "fjEeW-)-)2t`IekWOp6xFW(bQMeu}C&@~l-^u7lN}equ0d=Z_7AGMjd`$fPHU_~0ZE#a)Lv07_g#"
    "%3H@;I}78C4o#;f;N+wpCRVK}>8&fD_xCtmme4AyjertL>dyE~^)*K?DY*@Y?+9;FVYrCWy&xkk-"
    "iE1`ep`MQv-4N8L=jggIANRlsw6h8he;!_zo4-){j|UkB~sFAzryLsqo+QaGbS~C-x12<gQw&{q&"
    "`aX9-&ts3eMQ-HiDFwxW8l#Lr%jP7dP{mejK!o6~kBfXO>sYwm4QmKz%_ZE+a7qk0LJD*#3EUpze"
    "8{x%fWH0NbV>u=W)b1Nqr_tC|fGK<Zq-t<EDU5M~{CIihLs61XiLfO6dosy{-U*Xv-leeO2c8xOi"
    "u_soVSJd8f_#dXxtuM&0BTbE{+T;Gy;Z*`<9tSJYed}yAqYkenKKv{%C#6YJHK1eHZ-#!cEJ;{%~"
    "=Y-F-$bm~8Zaj;utgRz@M`Jl?eVltU3(zxw5HQ`EREXU@0%3P`?2^)RFu9t3z~c0XJ=s0vg<Nyh5"
    "c7D*e4hB;Q%(uMjYnfQ^~KUyxF?_#sYqFj_^dH$WLic~<}Bwx<B{nH`Xi`*BN?&}x0waE<}tQ23W"
    "nClHLNi>8k}<s*>e9<+wKU{;r$`2L!jyxAKX6TW3$V2sxu&pp;Tn*T{ttR*Kg~)SGWl^=A;?idXU"
    "(mtowKQ>^1sL0=|NQnJsM)mv6biu9H!;Ck<GyAD3))jU_?fBKxU{#XyvLvX_;V!?xRL4%Xo?jzn-"
    "cH#g&Jt^1R%b<Gq<b3|l()4!8D0t~l4p2?xHq^~I+>bWC_wL{eG4e}$8lQFn3BJEEO{5iJBhqHM="
    "@V80{Uu6~2OvY;?5wyN%t#4UA$7!(?S_D9j@ZM46`^252zk;Dv8%)C5s#(q1N@fpD>w2PA#5TSe0"
    "+11=OF!t5F<P(}%AG)(|0+1_@qVENwrL33;g^>0<r1NcYL4`N-ZLm50Dw*EIdA8vDj(SpPk+s-TJ"
    "JKNz^v(^;2Vh$?pE`8Wxi2Te{jPVeX)HL-vQUo)&}^ZyQR_UGfi&qhzs{Aq93$c`gF2AbDUPWjXD"
    "ra{-jck07pV`?Tc;1)R`VQUu)ls(Z!u6lSnM5f^l9hdXT5(wAdm&l|M{3`$|r)Luxo|EvaqSWgW+"
    "e<?X9{@snRM0-;-0w9wS=C1i1x_v9#sHfac2a)j;z-}l};40YoA5bD##(WcFnc`$DBBcK>x6HQpR"
    "LE~$^nAhKUa{iac2K#i8bSeMPAoeZKZf9<R?VLpPTcZSGH`SIm%k}6W4I3oFCc!dELjIOBfB}?r>"
    "!7n6MlFJw<vHtu!6ZD5O_R-GZPqQQ1&@&?0yglzHlL3(jOeTh$x6mx`ceFs?W|UG)X=$<l=23!oX"
    "+g&_2R!pv^z{&3{el+9z~AD6|1KP;1`~?6>#0!^^op;QL!snN02Bt)t0XH*2r6+@7t&x8xy3ou}}"
    "W1wnbn7a#Xu?%uWhJO<{|@%A(7!po2lc3@nm4kJnKwhPA2ue-c-r%iOpsoBED8p_)f}Q|emzJIgZ"
    "b*iye^4yZBsp)}{{&7}I0>8PM?19>%xE?L{qF;+@*vj#3&_U2%H{{mA`Sq+*bT(zfYng{-6Ss1KK"
    "bvL7UNj!%c<u;xY!o-8(_kUi89%qa#3k(aD{cp8(kJJUD!9263gJM%Z5yD@kFJcg5R|h!70Z_xCL"
    "Z;tS2$wjVL{6Ctc`)aU6-3aXiXV1jF5HqiBASg7PXrL}XXgV7`nn)cZ)w7U^^v^Zj~rPl%rJqF7P"
    "QlDP0}$?G%GKb3db^g4Ao4i+VTx$$HIVPSxN8GhGhIeV_7SH_|1gpoxir0`8)20?60XkxOug<{BX"
    "kv8gp<By58i1IW)?q+US$0-eeA?QV@D>?5e)X-R<Q$d8w9Pd8|fbg2>5w>Wj0wVHp;THC$!^>$_x"
    "0B?vriOwHK6$qG0rSn){=^zZ%CEg)>eyxmv*I~H%){0XwGI;owo(m$cxMHdkRAzoSg=s|kZ5ZN?p"
    "W+A5`i8n6)>;q1}yOe8%(4y)HnI5k?J4U8MSefNe^hVUo_1u|l38YbStx<g}g8H1pgLvne&GlNFy"
    "=76jYwW#&XFl2gI#dr)&%VFc;fL?r2ej%RM;QHNXN6*^ReCGu2&LD&C))7kN+KDMce1PbPa2-pP<"
    "8hueL(*#Ia=nX09$*kcK}_rMaOeq%;A^Bfb#6Yk=3teDBloBp!2q8cBih_(~P`H>GQQpW_^6+#e="
    "-<vHy>-kE(tJ5v^m=lF(L0;zxEWUhl_R&+j4wL>Bj9S-t*=+vzWB6!5f;eji)_P5JcS%L9>^kDgJ"
    "-CG&$MG1X*zGvo||F(h(CU)-q;yK0^ASa$pjEb-CUkzz_c;1DVfz~lW?@v&u_U{54=)nVA?FOu%P"
    "Fj8sYu&Xn-4>q>RsV(c~+W=KOroXg8L#Pi(b)8VNBPip9sTC!cWe;&Q7Yn>Xcy|iUTy{fwtOco_R"
    "p1Nui`oTlrRfUii(<pqGR0bNPJc`KsJgf$xIqqa^`ixk^3s?_%W%oBDESpTA)~8x=YisAvef!X5G"
    "18XeJ&`4-*;oPMDI%V<(kds4eXg+%j1>5qYU%&Ty@y17RX!R+c7X+H?eiYY7SLn9qJ1%fDbLFqp6"
    "A~L;emT=(>fdZD_^s&HXYUUL6xSdgJKukZW?v+4ZOIZiTQm8cmSq9fa!*EgESRYL0R3OCTDogJCP"
    "pZZ<Mfh0`Q%)W&0?bM0zifl&geH7nH$x#@^$-&Z1AinSD3FR;^6Kyc>b_zVh>?&{^^Xu7Ew?1maI"
    "F1H;TQ@S$>6yqgpgOUNTGe?t1o-O*$ssvP?3qH68_vq!a^o)3K-8O?j$a9<%tOv|2xnU}Bq|rVkK"
    "Uzxn!%{-blXc6GGH+8_HC&$*?6rR8X3$&F{prs#uOhe!8D0AjS-TZ;x>x=`@|E(rdbe>N&cJs0UK"
    "4Logx=~!fpOX;ZKpgU9=7dyC}w^P-gj+#8G2;#ZyAON<<`lugZ8Dg_kk*<22_WT{}(A0p<6noZbl"
    "2h*TH<?`%*hts8l6nA(6!b82B>^p6}e-O3j}|^=nmbKh(Kk?U^Y*ck?3N5gzwL|7=@vE;oQ?VKim"
    "~*fS{vP8p>T<n(-Sc|2sv?{cSbVRmLr);RmVZ}?S)JmhYPty-yg2&)?MG?lW><kP*6=ij^}zc)AR"
    "`+zlfOUDic16?a2fClZ&GH2D57>XdOIBvy&5Pur?jW*4FEhO-O`RkREbxhm|`x}<UvfsMM{q5-J@"
    ">h=Mt%2u33Pbz@H_S~_4#&=~6&Je(+8J{4-6D|WjRtze<jF~D32PdaWXQekbiJ*|3dIZpx`Hq-f!"
    "8Aa2-U@xxp%ywQsy#0D5p#3&Uau}VvJK>cVOIykkSXbj0{<5webj!4*DzzEihrpMLo}HqtjN!Jp5"
    "k*v)reoK=U0vUZC~ZW$^I$7%XNS0axM#R|MYOFP@*NlDuj`P0{%vKkQ2=eh_CDlw`tYDGY%z1%|U"
    "uc#egG)I7Ny+VIsF-9FJJf}wYAN1fa<=B1SPHo=|2Koj|xAtL&^5SE!O!u(KpnC%G!*`gi=Uupwh"
    "aUEpduXg0|BR7|&7Yr_Fb&!$B={g4C^E&Toy`#2nJ_657>;Np4e?#_U7Mgm{eqdR?ozYYdJuJ87C"
    "zzEmCD^F6AojbA;0}R*HHT(yX4Z28+xp#-UP0di#*vAuuLrfga-(<O>|dUKo*mjqvsk7(%lwCR|3"
    "S@0!PR)@WB0!h3r<RvOaHg(cA~#&@KCuCmLWXA$MotuL9I;f$`FlI5<VNYrnfUo=wJKRq9t`MWUu"
    "3TUm>1pZei=hYP;z&u)NVrrA>M#8Ju{SQ$M0NT<>J7Zjw@0Z#h47&R&^P4G>ma?}_vXG@%^0iUtV"
    "RrzxjfoegY_ZG0{Udt+u>P=b-}Ej0;sU$xOb(Bf{iY^9Tvlv`Glk94Ae`!E>xqFQPU1{Wds!XbVz"
    "tUH}{)T$C%`b2i}{%3;i)Gv3+D&NVzBl)Bihb{}4rg>h*2Z0Q^caJtP;hwfrk;Y1Z5n7fDE1~*V("
    ";;7dMg(_EEOTeKwFdpzVPPe@w_jVoeiOO;$JdKR(M4qF6-2PFY{m>+S#L6Lruexk&|z>eno=8>pJ"
    "l&jrr`nLnxfN}?!x1+4wFBB*Q!~oWHeHGj9;SXS`z<9eLNm*U4*8t+p*NVdOC}b9l-5I`9R4=eSt"
    "Uep{22Ee4nJ3=Tq~UTG_~lMJs+NpMqWj8SI@rl>)=R8|Ob-%Tjq~zj%NHl!T=j7%+g*hB%VwOQMw"
    "n`zS0}ai9;Llbwd-ZCMqPu=rJbn-BRC`6_b$7|MD?*gRasN|%ei{K&HxdSHC+*L}XUb&*kXA)w|?"
    "2FetsQ-wJUPnH=&EgI<tZS;J=F<r{cPJZxxCE?fLp9?F}l})WTC}ShEPuvc>&V1ak<=$Y-(4IfHE"
    ";cK=YxRe3#@e4ve8&)(iB}6gCSqk}97<=qp}C~0WarH0@$v5_40iTc^NL7&1klNq{0-lT{pZP{X_"
    "koG?mVDuxn(V%l4qP-Hgq%K=aMhV*yR$yvHop`(f(A|^?Z?1OS%Vve)V`{?M*pTTjV6=LQ=)HU)D"
    "QxfVplXpz(&HFj+=*`D$`^z}&)Fhz*kL!@R;0Fu5CWAdf&s7~y7Q@2IjODhzU-Rq8f;l~!Qs;)~C"
    "FOzri9R!A_)gq0hf5D^kFIwfG>S3mtjs|R-DC?~a<+Pkr~%&Vw34ONU<8~ZOwQ2QiCY@>fR@o2o`"
    "9QivH0&6!ADuE9Z+i9Vnna<J^mDZ=$Jl-VUkiZ)7MrSLR?nQ5z7n05B6&ONx67j({F#yk+aJN;$u"
    "UU8!F4|1S!;wN-Jf=!L<f~WZ49>+{OTdMiu=sducX_^1UAtvVtd^EqL51y`Z)(W*5zM733th6^qi"
    "6SD5NXu5T5vzj&z)7G&GsOP-<^H2s8cISnjk!D^36CXp>d)}tz)9~RPJRsh{H>dTZ~^FTFV_|AW;"
    "oWMe(IhQrHj>-}+T+WYMrD9J16k41ZKYt(-(3#5fCyLY<^nP3Q*{cb_8GCypF+E{r4u8NEd)D=%m"
    "yuN)vKl$W2)x94qM{khNI#B7r&X&9q}tB)JlT<TF82}d(D;i&yLyB;j|`LHD|W3>ECav-@o>OH(!"
    "$2P{Q`Tr}j(wHV5e$^`C^y}<tF0Vf4^lHzt{SOke^n8$fr;YNg4ljZUD^yV|cGT=TOQJ&pmB34K4"
    "NL^@Ya(|yJUMSEJ~erO=;DXm1=8$E;@I+}{pgniK|XmDwUR@G;7W=z32}1^-N?51D^0dN9GElJ)v"
    "6im!Yf-USu(r|x(X}K7_8VcG*88fZ><o&ASv#h#n3ynw_K4r-)yRK^S?R;60Q(`61<$5SzE(*7t{"
    "*{bRcBqNf`r5(5KX6va+Awpg)6np;{v@a=n)fDdBSzi)8x;psJZ=vPuJnAS*&;YA2bb32;JCK|E6"
    "@eV7c>v0`eW<5oM65WoL}WpNCi7cIMuaz)_>PeH+NJV3ulkK-6SJ7&?<Z*7nPsLtb)Pa99W10v{K"
    "A~L6qjU#n^&8}@;&mu!RS-gIz5s0x$ytlu#<WE0UM0n09nTHg55{=Q2$kKVrRTPjR%II9p1j=y(J"
    "`~RUJ$(M@h_!`921cx0O}<-;?A?zP_%_WX&l}GzIk|pWlcoN5f%UQIQle%@hc42Eq<=&x#=7lQ#&"
    "kcs{Dn1g&{~*$tdD<do@r;>ooU3u2x4>wTD+rbkee$uu)*9>dj*o6GRoG}kz*L2xVRfdo$u;a+=J"
    "F?)>--{e70Qv9SyaFJMW+^)K}jd0Asxy?Tl@|by#p-Kz0-niK&}^J=)3H?ncCZ4-X~SoU)Wlf1<?"
    "cOoLcWb-Lk!{^f(-W7L*IbQdbk=}}W%wd{u5+nTt2i%fPu9_`8f1hM-g7-QpW^{Tog3g*u;a$9}X"
    "irNt)SNgI&;?^_{!&K^2;_rI-m_}TR8<qp${6%0u6U>)_+t>6>YCeiOVi!7lOyD7ug*EsH#3)tnd"
    "h-`0{?`#hJSil4UhOjs3PRGK+n%B1<-K;KtY$Cd6|ISj)M7~ur8z3eWviD7;vJgF8Ii)0;3vLld="
    "~gi^}C>Y8`lMiJWuXKCqN#%6YqKejUh`$ox8YP+W{D=L1aVwUY!nKDYIGfO>;4+!~$AOzqbabMZi"
    "sma_{$vBJo-jA{;C>m8?<Qe+@QU9-JbzIJvoA|A1rh>8Sm1zpBp9@w_IssDr-<WY?EkNd~$^e~~Q"
    "{^g-jI=kt>2LDz*eQsu^oiGhrOrIxxaY={Z~9HlC4OH8(-6qz1)&%kI(&i~R>Ve6ht=@kiFuW9@8"
    "m|u7lE$PDh8Dj~llC57E>~a&qR}9~B*&FI`JM(iOdM4hn!e8;So))_TvE@^#G^SB_lq)v;9dF0*I"
    "BZ*#N?|4JG59LcN`0IQRk11qE(BB|KaYy>T-pa@&K;aqk$M$uqxw`{#$OdordiG|WAfu;fq}(ZJ|"
    "q%UBTgJ_)!260KdxD1xr2;O%Oxc;TG`0vf=SLkZ52>SVn@Z`q2mzUE?gk!%(7~j?OYicn<B|mX)l"
    "eXj&v!@u}^-wdIPH-mrRlLr?eQdGf0u=uQRVwUwi78ObZ2IIIk`M>Yxrpqs5eu@lpIG#xHcI9d<#"
    "Ai*(H$OrT7XA+W!^cp?J$dJz%AQ&E6;&04HrZBa?27GoYhIs9hmk(e0ut?^IdLw4|#bbAXkaS<RJ"
    "C@zghCy>Phx#zp;vacbu4|Tn%Cp{Sr{g?#b+MKxH)pXY!=R>M;bSbkTtUtm4C>Im<O|5k`m2lMqF"
    "G5_k{EO|&eZ;nw6p6PKr;g*{fIS;<-4N;(<;&$KnN0MgCEJ(#5?ar6KF}>p%H?cdol%>>0jy!Ply"
    "RKXKLTj9+036*&QIPJoW_4oJ&Z+z3AtR2-^;@qODbZJO01ympT^99*y+rJ)-w~QDa%(>Oy4GepR@"
    "K*vb~?>;gW?|05RnxS#f{El;2a^w(5x5>?y%PYOLg4aPzxcE&TobgLSj(crM}JeUheh3oyYRa{=^"
    "sXaI9bE|ea5RWb46u=@UbUTWFiITLgFQRnL?Y0iks!1awClV~x=f_h324=9a%GHXuAaVsS9uT|{+"
    "RQE>Yo7EZMNH$u{+#l|cDQGH}9eXOJ&7vUaPQtFKzUK34Am;y?^vD7fifG4bg&>=AN8nU`^gz#IR"
    "d^RNE&^HycyT9FK;)7mwVb@9tGcPV*W$EVkIb3q?Y<G9Ewe&l%Ds6M)KhSRgax!nB%B-(_RBItMG"
    ")o!KHG!*LSb?sKNQ{MSKJ1=AnBQ1cQCvn%i*>?ztSE#Zx~cf^>nlC|GYcQa!I>Vu#r;iEZk9*e{L"
    "vKq}!<!sl9HS&Q#5CG5&kg%whJ@T}8+I%nG6rIk<3)o%8P;6B4-ZR%(b){UU_{4(lPpPfg&J-XVB"
    "DA_#WzQsG(G)?OM=6dbHIjBr6-->{>rt?-4v>WQ1jVx=RAYHv-?8S8w;kkbIk1~8ZN=y>E6pLd>v"
    "c&XD+AlY4Aj$<^81^>obQ}|7>lc{jW&<ae3Pbw4W5$ouJgz61*WrlZ@!sFl)<nddWStPRJKrlmy;"
    "!(`^Jhq_+w;>$Wn4o-dci*%4%P8_BgXu?2;IJ{GgEX<Xf^)}&;l^-_&Uvk?OgbeKkptTOH$W8+S5"
    "tmnSR1P_YKS7FDIxQlu-I|PYCa!qz3ke|opA;*PT`V2iA|ttd|rACxOs~Y<%cg)`7w$L*GjxO-@^"
    "g9Y$DatKNEUxKwXz-wiqJr7EDpmAY4rLXoW`WB7p6&THdgpqO~7GKkY$VN<^PQ>+n9y2nSC#_XR<"
    "Vk?yo0zubu`*?W2M0Czu-oJQ&o3p-xQ*?M`@3^8=TQB^$;MCHl;4Xkc~3t?KY)n@BpAM_bjy8N`)"
    "FLS9gjsI|jk-^!bWs>On=@nXF9qWoc&gIwj)7Ixm=`yB_Ycn;9O*kK)3Ukh6A^8VNn;);N!PEdSO"
    ";P$T!Phi$6F77xAQ1(7BbW%sJ9j7+ct}FHpo;vFP_xvLK*$@7u2&Uev=;Kg*-3pY!1jl1+pjBT63"
    ";W814LhX>~155WY_>jt_@E1RL&QgH{R;<?VM7;ziJNNk4}Q`P%#t*Tmv50xxav<yKcQ2D3%&i)>f"
    "a*P$l!*92X_~@p`qfzaLd0d-U>BHgZ?98;IXEy(jyXZN^I+(daOvS+CDCw04dvoOBC`?;_4^nHvB"
    ">%2iAuy%v8e)(MR94>~F`WKOdC#RfCb3&sdgDYr)+Cn<b*>D~2=RKg$Zn}Lp3_wc8ho^;Z$wWjW6"
    "RK$98`Rj3_nBy19b6e7!hVH{kl%!V?&V*2|6AEavp{io-YvUEDbMH)TS{sfER_BniW3s4d{{I$MO"
    "*vmen9|2DqFGLnBFp>yGE6x=me#*GjbVhP)vSsxjC{Ep!J={E$&?0VOg)bOA~d``%OVzoI{MPm{8"
    "bgd_#0qFrGqE02HhkrnGS6JQyTyie=}Y@k;QuU8o(frxL!KQ%igm-fqangvj+Ww>`Uy%IdNVJy9#"
    "3(*tQWU^^7sCyBXUyWVtf7KkTUz77J%yf<)k!;1PF4-v3b&*6%F){+?(*)Z6lh=!)1k`J!9o;S{Q"
    "eCLx`F(_=}~gv}DV8`B{J`z*L@Q>OBGyjibb-bsdrxP-mXU#ejBCU4F2nj+9A0rG5YD+ym+h<Hoa"
    "0ZTeNynw(#E1UfQ<sC$=1oAsp4tDmC7JG+oghv-u(}IpoTV9OW-vEkw=^tP4;HoP&NB}<Hyu;Hp*"
    "$w;O+gD6wyk-iaBcE>VS-b|swzOz(+Sn{%$E&F}t`y&Zp)fis2;U-~oj?)bT|FT(4|lq%>P4v@-1"
    "&0+ETXGDu680tW)r>L_^sRAAL^Jvaa-w+p^%#&rFNGOdH_ctiIU1)|46}O+O0Hb#0yjUXUM$8CIa"
    "kh%Ibdh!giZ5y6XBH`o|bI><5Glcj!A~b|(GxqTzxH^Bs{nDNB!a%IJJ2fY_*G)r2!pUdc9xDBW_"
    "#JatC}$JRGt*~tv}K=T(Uxx!oTJ?yEyq4h0m1XbkW9S9*~?%&t-`ZoB$q;itR%+D9$&IeA~X|)L%"
    "lJ^?zY~cDV5&qkKv)et@f6un6;zh<oE}V-m-chiaTPfa?QbxIG*!-%3EdaqlSaC~yB5h9`1$D+nC"
    "lL(r=2Z53_ku<s>Y%KPknL^=x4;?WwU3&0{8(tCZ9D`jyWuNLg4~H*@U%%F1L-O?BqZmE!t;++x("
    "?dX*BpOLV>U&u8=Pt)k^bq)u07w-C<T5Ka^M!k=wE|aj`wF_WxWhb><Q6)c1ZLOx-xX&O3SA!?Vu"
    "OSE)vSWxfY{tN!>`u8f>O<Mp)8$PY%&-6W%CzT6ubKGw~UYfx#PnnEk-e&<)WEs`l%Ulo{TD3a81"
    "W;j|~cpu*Qq4nVh+*@ry|G&DL*O6;iGvYmq;w~SO&te6J698PP7huUAil;VdQZYjw`%>i%W(cq|6"
    "qV|t6;BNqKP+dR16xjO$Qg&vqr!!~w-2AC67b`U<R8B<ZsDJz6<hQzi--2^ynX9602b}tB9;UxUu"
    "f`IeRQfp>DiYuue<MUs4Ir=c^yvcpwW@2aJjWNXzxgM`Dr7frj&7JG$!bNp$@-VF=$KCh+NPtz-6"
    "tFQa130YU-AW${o4u#Y*ZyeIam~`{~%E>o!E)7s*N(G=|-A1dJb(ZpQ9bd4XI6Zg@Fv?!0FH<Cx-"
    "-tO2WfFQ}M@>10OZzn+>~eS1}{j*1l<Gvs;vipZxwqW{)^b)l<#Af{i9(8DPr<@3au`R96u?Vc%p"
    "2E`VP2rn>l5n6#3;fWHV$L*+D+fcbq(CY0`HQQHbg{8<d4u?uVC!(ITIg&(6$Kjh#bu*uMFb-d>G"
    "3%N}4FwgH%FiiP<f0+JU7Zkn=HKew+C+u_KXc^<~7~k`)^DOZV%0mjQ^r>?Uzy>2OPH&!Bjw;M8D"
    "Dli!|F_2@Y_|E_D7gmqN!m%V2VIz7v5SBejY~z@+>MDkNT-ka#JBLq@^@9{r*mghbb{tah(Sc~%N"
    "9g!tu+Cjd>IwmB6Yme&q7}THN3U@klWRY_}SC)@l-Q%!!aI<B6J^YuQ^5xXXTC29Q+%v;?XSBE1M"
    "G|rp<Y8Maahq!XS26l1g@XV<tu2gMEQ{^Ubx(Nzd(!lSzK;TSMd_<%Qxz^zt<yYtQhllZDS=Ni{Y"
    "YdAvz9V34YDFX~>}5(_HZ{dZ{!CZ_kwb6xFjZgO~H<f{-Pv}t9B<^>x)(Ha=T)FS&pJ#@gkO-;k7"
    ">g_{Pvg9aYH=Y-@tK0-osv2^oqC3>dR{*sLMw~hqLk(V#3a@+klJzKrq_+VbCUXHOjtbhY9TYt}h"
    "?F?Q138n!6jbo-Z8rdW`Q7`h%#Drp!PfWoH+H|+JA0<KvD>JV`WkLZZ!8BQ)0fx-B+%ZoW9bs9Oz"
    ")*?hMH~l)>>w&;Y;5ZL7S!lS}lSsx23xan~4+91V>hQk~wpV`5u+6^DQb_i%mnJwddb2407$Ik^k"
    "Xx2}U}LhoGW-qL2MYSP3^9^b1Id4Gh^5te`z8Zj)x00JOO(j27Y3S`}p;I4168B%2#SiRM?|9hh)"
    "ET8xQDlvq37$>bN9rx=&oy3RK~#Kk63QoBH&>A_Kpd^9qPYx^iJXHzcH6aZNy21oj@d{fUukJNru"
    "mx8Ce{n1HkEoJDUj;RfaCN*@VMcN;~^9z8SX?ge#uthm^1gy91gI?ppWiFh>XCJTupU;kV(zl@I2"
    "=bQDyK&H8x(#9*6|RC86)eM#UMAGzJ8m!Bz#W&TlZHT~KyEZ6M>{k8iX1B_#p!D9le4PyLjLOdW("
    "Le^GJf8W$fGT3(tr|}igHJNp00W8k1Y7v+sUZcYdNX34<cBf+IoZ8gCgkozji;L$ivu;+53k*FBM"
    "OFd4QD<Pr8=Y{#yMSgKC>2&hdE_YH)De`Gz0HW-H0>HKF(d9gcxNysKr^`k)mdVya(ft^Ft9csGX"
    "}r&IhoNo6}0pXUGJoz{V|5DYx~A!}G3xUuG<-F1oR8r9NdU6jPp{R#QRC_x%m>-PG%v--=ywAPj>"
    "u&3+N==d^r820?WU_e;$=2iD@wxu>;!5|{o$g&-MdN+1~IRyiEBT`FZ@Y4csU3%i5mtxrb^QFY>9"
    "gStD!Hn{rG(<0NC2|@^)C%E77a5_Fwspsn@KG6r+Obrw5Dq8M0{xw5#~jb}H7wkJoS6OYJSOceVe"
    "E-0C}q@|>?Pg6%6K(pu^H6yI)mCFa$&w)QN1zJ?LB;8FYwHC-#ObBwfx_7iZPGJ3{}N6BigKk9D#"
    "d_Jq=p57MmkOaI)%o>(hgo`zvbw((8o5H*Jm##=Em$_#}(22Cl;oDEQKmlS2vKtI^9FwT=JIG=VO"
    "jcC*4)$4Yn9CUKMCjdNQE)|FXGL+Ko;-Gd%xq<vE2Rk4nFQb&iapDTO6DU3{m+YwylYCOa+aTLjp"
    "4$H%Ti~Ru4K;j|8m?mShgsE?=%l`Pd$&xELnThC7`_f4sKi&XgI^?gOI;b<nBs7XE&88O02eY|He"
    "=1|M^7^Z1nx1zx=N6a5toqaZlapqr3QwOT&1Tl;NIxRKd#ken!-Gpz@I6Dn7i278Suo4VsX}?o!*"
    "uGO9}o?F9!)2e;?`!#{3IC{qb(%){BeOf)5ng?kfvStD&-CIWJu7;A>OW+w335Tcb}xt2Eb3AuqD"
    "JS-NKi6kp&1X)CG1)rsWOEzfR}+ya1K#|AhXbXQl=6QIG+teYxi@_v+!gnK5c-$04tlnVH>HZ6sF"
    "dA&@vImD&Ll7D<x<Q()M`BMYo|annMtH?n3F+6o^Z1uR9?P-Xx;gZ=Zaa?m9YY`eV!XDkTJzLOR("
    "&7C3YJi-$KEB$A#?Hukq+@Ov`n~8)HQS@nbRfE^D&qXBj?V60X&S#wQd+=_u7dqSv*uCkk*7D6WB"
    "+QVYXKL@^LHn2a;A{ztR=-*rtpwK#O`g=-pYNQERJ17s9dt`wU@sig3e*$^rP7&vCTK?OA9XFHRI"
    "@$`4TOp1dCUM0aeM?#^JXXNk#QB@2+Z<Wd5YW+oCX{<c7vKr1lZP|oGUeML+h!%Lgcke-I}EJfhE"
    "c)AF!O1xcfstMFEww3xk+Hq$~mn-*REeEIA@<Uyj}LhIl8h`Z8?D#IFSP<IWYvyzZG*kYoX0ei1Z"
    "eJPiJMc_$_gWpVxQ3QOz_Pg0c)GyK>pe*%6OT8gBFK<O64pN0QAApqaIo;wwyby@x#vK=N5(UiXV"
    "NDMi6l4}dtp;{ceRVVl~2<b;%eJMKm;TY?Tv0|zW(EqySTieIMCT`;vDlRc%(Ys3KkP0uZXSR?jM"
    "YJkdd&}^1!htY^*NMK@$6RwxfE(rH)<(xe?Z10(wb3W#(AcBP@T4#+TyhkIRQsg=op9p+b|mP&8v"
    "7OHDguYRSdW^O42`b6T=Gn%`%$fZu_6cHnCpBgmodf^%#SqWnO2{8KZTJ)fYH#x;-`1fLzx{fX5?"
    "y%3oG}6!oU<|9hP_;vC_lDZ`TK8F+}MC+dS)&1y`EwAFmF%HQW(MY`E?!iM%UF(aTv95pwDn0d+g"
    "Ipo{cYdxmvEOf3?W3?j)&@Qtz9P<Jj>s&`}@KCII{UCLn2#(0vTF!}ybhd$9G4U0W`lA-RjBb+`J"
    "8Ap85WLm~vs7%jb2#LRkWpmD62>`b^KN11Aq$ywv8?XKx-h>Ve%gmDq{Utm<EGUPf3o-{90Fuz=S"
    "7x#X%1j}}^N=9o)V@U_Hx*rhX2->tJZcsved)o<VwxKdv4*X3%EsjAZtG7n-Jl9nnzvBs!|%#xUE"
    "V$F?GJ`6RmN$}jBZ0EKN}ds7Y{4HQDE>n$qNkPNII>~Aq&`PKyn^_V9z6=?-dAL52~ol5-M#ob_B"
    "(t=*4&cCD;1O`Sg@6Z!&IVC!>dl>bYrxWqpo+@gv)-;ztDpBD>UB2(pub;ok~(kBj}u(}Y**(!m_"
    "XW3V^~;fTFuK>kh}_7>wJ-5%lL&X&@v@Kaa|;$Gma^Yg;Ni%$uwrs`1~Nrp?gi#OS-jf`%#X>C>R"
    "9K4_1$}?l#h-Oe-eZ|9KjBJ(e6mi_!b2U0~XB#(}2}2|R54r+mfs^?I?AVU=L@$SEpcc`3DOsFk5"
    "~bu8FI+af>&}K>9-nR|9BY`~`#0*)R&1Y=R=@oikyA!(7;T)nhPc_)22vJHHO9*%IP8VZU%W6Vqc"
    "Fx44QxcDOyD1&2f*Ua;&WL5UN8;Mgtj6G<4tQuw{%_LtvbcUQ5%ODmo14>S<Iiuzw=1wX8ngK328"
    "X<JX0(Mngg@fv51_@T}ifT6eCb8fmLI5W+{Ev`Br~8*Oi$H`w;cx^o=E7f?81>x<S;l%%4Vq45G}"
    "s++8RfG64>E`Kfd8pp@)<EvZ6u^zM}C#~9fW;m|yL+QuBG^<eVVycQJ(KLoeShkkK&YVr0^n+gOk"
    "Y#f!s8rebN$a<}-Yo5a`SVd3txFN?X!xUq6Z@aJJHSC@?#omC^Q5UCyE{bJtbiaI_=h-Tos2xP#Y"
    ";?ji#i<~G0vy7GJO4-EFCyd68rlVMJnw_gz}5d0x_u=mqrBut`rPgOEcy3NlddIP(*Cp;;H$gNv;"
    "_X1fF8iiSBtMS)Mn~L%+DWHg?1AeC6iAz`&GE0D{`j==bw8dYJg1dxdNhN#YZK5E5eo!nE{`6v^8"
    "W-&gNv#7DqoiV*-I6(fIsfyee`{t=W`DxUg)0G?S*@MJk+zHDK};%6J%TLyzA_Tt9A2Gz9j?3J8A"
    "tqqb#RHw3n^ZZLkmC`{LYI1n`)N>G6X=!>P97IK`BDCdjHOg$Xg=K#q&1m%YS*Td!LF(VZI@V1D="
    "WK@vm>u&!wEuA%m$QQkq=Bx0RN$}URw}Oqobj*fPd>0_56_cr>g6nBLI=?~IRtDMYwcqoGgfmvqo"
    ")?Kn=Oh()&Yp1{^6?;wWj;Iv-Chf%MA#u{LH^acl-+o)EaEl;J=Q;}CUwH{aNU?D0vk_j9wJF%ma"
    "TLIerGz4)3{CWi-h}9#z43KgXBC%PNi$;Y6eq#Dh8T1h5fnkWDp?c-|&qcc^YUr$eR#sNM$F&QOq"
    "a1rqiz3(dXRT"
)
_ARCHIVE_OFFSET = 8
_MAX_STREAM_COUNT = 100_000
_MAX_DIRECTORY_STREAM_COUNT = 0xFFFF
_MAX_NAME_BYTES = 16_384
_MAX_UNCOMPRESSED_STREAM = 1 << 31
_MAX_ARCHIVE_OFFSET = 0xFFFFFFFF


class SldprtFormatError(ValueError):
    __slots__ = ()


def _decode_signature_table(text: str) -> Mapping[int, tuple[bytes, bytes, bytes]]:
    blob = base64.b85decode(text)
    if len(blob) != _SIGNATURE_TABLE_ENTRIES * _SIGNATURE_ENTRY_SIZE:
        raise SldprtFormatError("embedded SLDPRT signature table is truncated")
    table: dict[int, tuple[bytes, bytes, bytes]] = {}
    for index in range(_SIGNATURE_TABLE_ENTRIES):
        head = index * _SIGNATURE_ENTRY_SIZE
        file_id = int.from_bytes(blob[head : head + 4], "big")
        table[file_id] = (
            blob[head + 4 : head + 8],
            blob[head + 8 : head + 12],
            blob[head + 12 : head + 16],
        )
    if len(table) != _SIGNATURE_TABLE_ENTRIES:
        raise SldprtFormatError("embedded SLDPRT signature table has duplicate ids")
    return MappingProxyType(table)


SIGNATURES_BY_FILE_ID = _decode_signature_table(_SIGNATURE_TABLE_B85)
SIGNATURE_FILE_IDS = tuple(SIGNATURES_BY_FILE_ID)


def signature_triplet(file_id: int) -> tuple[bytes, bytes, bytes] | None:
    return SIGNATURES_BY_FILE_ID.get(file_id)


@dataclass(frozen=True, slots=True)
class StreamRecord:
    name: str
    data: bytes
    offset: int
    payload_offset: int
    compressed_size: int
    uncompressed_size: int
    crc32: int
    signature: bytes


@dataclass(frozen=True, slots=True)
class SldprtArchive:
    path: Path
    file_id: int
    format_version: int
    records: tuple[StreamRecord, ...]

    @classmethod
    def open(cls, path: str | Path) -> SldprtArchive:
        source = Path(path).expanduser().resolve()
        try:
            blob = source.read_bytes()
        except OSError as exc:
            raise SldprtFormatError(f"cannot read {source}: {exc}") from exc
        return cls.from_bytes(blob, source)

    @classmethod
    def from_bytes(
        cls, blob: bytes | bytearray, path: str | Path = "<memory>"
    ) -> SldprtArchive:
        source = Path(path)
        data = bytes(blob)
        if len(data) < 8:
            raise SldprtFormatError("file is too short to contain an SLDPRT header")
        file_id, format_version = struct.unpack_from(">II", data, 0)
        if format_version not in CONTAINER_VERSIONS:
            raise SldprtFormatError(
                f"unsupported SLDPRT container version {format_version}"
            )
        records = _scan_records(data)
        return cls(source, file_id, format_version, records)

    @property
    def streams(self) -> dict[str, bytes]:
        return {record.name: record.data for record in self.records}

    def get(self, name: str) -> bytes | None:
        for record in self.records:
            if record.name == name:
                return record.data
        return None

    def require(self, name: str) -> bytes:
        data = self.get(name)
        if data is None:
            raise SldprtFormatError(f"required stream is missing: {name}")
        return data


def build_sldprt(
    streams: Mapping[str, bytes] | Iterable[tuple[str, bytes]],
    *,
    file_id: int | None = None,
    format_version: int = 4,
    template: bytes | bytearray | None = None,
) -> bytes:
    type_ids: dict[str, int] = {}
    if template is None:
        if file_id is None:
            file_id = _DEFAULT_FILE_ID
        signatures = SIGNATURES_BY_FILE_ID.get(file_id)
        if signatures is None:
            raise ValueError(
                "SLDPRT file id is outside the native signature table; "
                "a native template with matching signatures is required"
            )
    else:
        template_data = bytes(template)
        archive = SldprtArchive.from_bytes(template_data)
        if file_id is None:
            file_id = archive.file_id
        elif file_id != archive.file_id:
            raise ValueError(
                "SLDPRT template file id does not match the requested file id"
            )
        signatures, type_ids = _template_fields(template_data, archive)
    if not 0 <= file_id <= 0xFFFFFFFF:
        raise ValueError("SLDPRT file id must fit in 32 bits")
    if format_version not in CONTAINER_VERSIONS:
        raise ValueError("SLDPRT container version must be 3 or 4")
    items = list(streams.items() if isinstance(streams, Mapping) else streams)
    names = [name for name, _ in items]
    if len(names) != len(set(names)):
        raise ValueError("SLDPRT stream names must be unique")
    if len(items) > _MAX_DIRECTORY_STREAM_COUNT:
        raise ValueError("SLDPRT stream count must fit in the native directory")
    local_signature, central_signature, end_signature = signatures
    output = bytearray(struct.pack(">II", file_id, format_version))
    encoded: list[tuple[int, str, int, int, int, int]] = []
    for name, payload in items:
        type_id = type_ids.get(name, _TYPE_IDS_BY_NAME.get(name, _DEFAULT_TYPE_ID))
        data = bytes(payload)
        local_offset = len(output) - _ARCHIVE_OFFSET
        record, crc32_value, compressed_size = _encode_record(name, data, type_id)
        output.extend(local_signature)
        output.extend(record)
        encoded.append(
            (
                type_id,
                name,
                crc32_value,
                compressed_size,
                len(data),
                local_offset,
            )
        )
    central_offset = len(output) - _ARCHIVE_OFFSET
    if central_offset > _MAX_ARCHIVE_OFFSET:
        raise ValueError("SLDPRT local records exceed the native offset range")
    for record in encoded:
        output.extend(_encode_directory_entry(*record, central_signature))
    central_size = len(output) - _ARCHIVE_OFFSET - central_offset
    if central_size > _MAX_ARCHIVE_OFFSET:
        raise ValueError("SLDPRT directory exceeds the native size range")
    output.extend(end_signature)
    output.extend(
        struct.pack(
            "<HHHHIIH",
            0,
            0,
            len(encoded),
            len(encoded),
            central_size,
            central_offset,
            0,
        )
    )
    return bytes(output)


def _scan_records(blob: bytes) -> tuple[StreamRecord, ...]:
    candidates: list[StreamRecord] = []
    cursor = 0
    while True:
        offset = blob.find(_LOCAL_SIGNATURE_PREFIX, cursor)
        if offset < 0:
            break
        cursor = offset + 1
        signature_end = offset + _LOCAL_SIGNATURE_SIZE
        if signature_end > len(blob):
            continue
        signature = blob[offset:signature_end]
        record = _decode_scanned_candidate(blob, offset, signature)
        if record is None:
            continue
        candidates.append(record)
        if len(candidates) > _MAX_STREAM_COUNT:
            raise SldprtFormatError("unreasonable number of streams")
    if not candidates:
        raise SldprtFormatError("no valid compressed SLDPRT streams were found")
    candidates.sort(key=lambda record: record.offset)
    records: list[StreamRecord] = []
    by_name: dict[str, StreamRecord] = {}
    for candidate in candidates:
        prior = by_name.get(candidate.name)
        if prior is None:
            by_name[candidate.name] = candidate
            records.append(candidate)
            continue
        same = (
            prior.crc32 == candidate.crc32
            and prior.uncompressed_size == candidate.uncompressed_size
            and prior.data == candidate.data
        )
        if not same:
            raise SldprtFormatError(
                f"ambiguous valid stream records for {candidate.name!r}"
            )
    return tuple(records)


def _decode_scanned_candidate(
    blob: bytes, offset: int, signature: bytes
) -> StreamRecord | None:
    header_offset = offset + len(signature)
    if header_offset + 16 > len(blob):
        return None
    crc32_value, compressed_size, uncompressed_size, name_size = struct.unpack_from(
        "<IIII", blob, header_offset
    )
    if not 0 < name_size <= _MAX_NAME_BYTES:
        return None
    if not 0 <= uncompressed_size <= _MAX_UNCOMPRESSED_STREAM:
        return None
    name_offset = header_offset + 16
    payload_offset = name_offset + name_size
    payload_end = payload_offset + compressed_size
    if payload_end > len(blob):
        return None
    try:
        name = _nibble_swap(blob[name_offset:payload_offset]).decode("utf-8")
    except UnicodeDecodeError:
        return None
    if not name or any(ord(character) < 0x20 for character in name):
        return None
    try:
        data = zlib.decompress(blob[payload_offset:payload_end], wbits=-15)
    except zlib.error:
        return None
    if len(data) != uncompressed_size:
        return None
    if zlib.crc32(data) & 0xFFFFFFFF != crc32_value:
        return None
    return StreamRecord(
        name=name,
        data=data,
        offset=offset,
        payload_offset=payload_offset,
        compressed_size=compressed_size,
        uncompressed_size=uncompressed_size,
        crc32=crc32_value,
        signature=signature,
    )


def _nibble_swap(data: bytes) -> bytes:
    return bytes(((value >> 4) | ((value & 0x0F) << 4)) for value in data)


def _encoded_name(name: str) -> bytes:
    if not name or any(ord(character) < 0x20 for character in name):
        raise ValueError("SLDPRT stream name must contain printable characters")
    value = name.encode("utf-8")
    if len(value) > _MAX_NAME_BYTES:
        raise ValueError("SLDPRT stream name is too long")
    return _nibble_swap(value)


def _encode_record(name: str, data: bytes, type_id: int) -> tuple[bytes, int, int]:
    if len(data) > _MAX_UNCOMPRESSED_STREAM:
        raise ValueError("SLDPRT stream is too large")
    compressor = zlib.compressobj(level=1, wbits=-15)
    compressed = compressor.compress(data) + compressor.flush()
    encoded_name = _encoded_name(name)
    crc32_value = zlib.crc32(data) & 0xFFFFFFFF
    record = b"".join(
        (
            _LOCAL_SIGNATURE_PREFIX,
            struct.pack("<I", type_id),
            struct.pack(
                "<IIIHH", crc32_value, len(compressed), len(data), len(encoded_name), 0
            ),
            encoded_name,
            compressed,
        )
    )
    return record, crc32_value, len(compressed)


def _encode_directory_entry(
    type_id: int,
    name: str,
    crc32_value: int,
    compressed_size: int,
    size: int,
    local_offset: int,
    signature: bytes,
) -> bytes:
    encoded_name = _encoded_name(name)
    package_section = int(
        name == CONTENT_TYPES_STREAM
        or name == RELATIONSHIPS_STREAM
        or name.startswith("docProps/")
        or name.startswith("swXmlContents/")
    )
    return b"".join(
        (
            signature,
            struct.pack("<H", 0),
            _LOCAL_SIGNATURE_PREFIX,
            struct.pack("<I", type_id),
            struct.pack(
                "<IIIHH", crc32_value, compressed_size, size, len(encoded_name), 0
            ),
            struct.pack("<HHHII", 0, 0, package_section, 0, local_offset),
            encoded_name,
        )
    )


def _template_fields(
    blob: bytes, archive: SldprtArchive
) -> tuple[tuple[bytes, bytes, bytes], dict[str, int]]:
    records = tuple(sorted(archive.records, key=lambda item: item.offset))
    local_signatures = {blob[item.offset - 4 : item.offset] for item in records}
    if len(local_signatures) != 1 or any(len(value) != 4 for value in local_signatures):
        raise ValueError("SLDPRT template has inconsistent local signatures")
    expected = {
        (item.name, item.crc32, item.compressed_size, item.uncompressed_size)
        for item in records
    }
    central_markers: list[int] = []
    cursor = max(item.payload_offset + item.compressed_size for item in records)
    while True:
        marker = blob.find(_LOCAL_SIGNATURE_PREFIX, cursor)
        if marker < 0:
            break
        cursor = marker + 1
        if marker + 40 > len(blob):
            continue
        crc32_value, compressed_size, size, name_size = struct.unpack_from(
            "<IIII", blob, marker + 10
        )
        if not 0 < name_size <= _MAX_NAME_BYTES:
            continue
        name_start = marker + 40
        name_end = name_start + name_size
        if name_end > len(blob):
            continue
        try:
            name = _nibble_swap(blob[name_start:name_end]).decode("utf-8")
        except UnicodeDecodeError:
            continue
        if (name, crc32_value, compressed_size, size) in expected:
            central_markers.append(marker)
    if len(central_markers) != len(records):
        raise ValueError("SLDPRT template central directory is incomplete")
    central_signatures = {
        blob[marker - 6 : marker - 2]
        for marker in central_markers
        if blob[marker - 2 : marker] == b"\0\0"
    }
    if len(central_signatures) != 1:
        raise ValueError("SLDPRT template has inconsistent central signatures")
    central_start = central_markers[0] - 6
    end_signature = _end_signature(blob, central_start, len(records))
    type_ids = {
        item.name: struct.unpack_from("<I", item.signature, 6)[0] for item in records
    }
    return (
        (
            next(iter(local_signatures)),
            next(iter(central_signatures)),
            end_signature,
        ),
        type_ids,
    )


def _end_signature(blob: bytes, central_start: int, count: int) -> bytes:
    central_offset = central_start - _ARCHIVE_OFFSET
    for offset in range(central_start, len(blob) - 21):
        (
            disk_number,
            directory_disk,
            disk_entries,
            total_entries,
            directory_size,
            directory_offset,
            comment_size,
        ) = struct.unpack_from("<HHHHIIH", blob, offset + 4)
        if (
            disk_number == 0
            and directory_disk == 0
            and disk_entries == count
            and total_entries == count
            and directory_offset == central_offset
            and _ARCHIVE_OFFSET + directory_offset + directory_size == offset
            and offset + 22 + comment_size <= len(blob)
        ):
            return blob[offset : offset + 4]
    raise ValueError("SLDPRT template end directory is missing")
