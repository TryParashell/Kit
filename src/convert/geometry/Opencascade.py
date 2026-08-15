# SPDX-License-Identifier: LicenseRef-PolyForm-Strict-1.0.0
# SPDX-FileCopyrightText: Copyright (c) 2026 Parashell, Odin Glynn-Martin
#
# This SPDX license identifier and copyright notice must not be
# removed, altered, or obscured. Doing so is a material breach of
# the PolyForm Strict License 1.0.0 and voids all licenses granted
# to you under it immediately and permanently.

from __future__ import annotations

from dataclasses import dataclass as Dataclass
from itertools import chain as Chain
from math import isclose as IsClose, isfinite as IsFinite, sqrt as SquareRoot
import re as RegexLib
from sys import float_info as FloatInfo
from typing import Mapping, cast as Cast

from interchange import (
    BrepBody,
    BrepCoedge,
    BrepCurve,
    BrepEdge,
    BrepFace,
    BrepFaceUse,
    BrepLoop,
    BrepModel,
    BrepRegion,
    BrepShell,
    BrepShellUse,
    BrepSurface,
    BrepVertex,
    CircleCurve,
    CylinderSurface,
    LineCurve,
    PlaneSurface,
    Vector3 as VectorThree,
)

# this binding exists because parser limits need one shared invariant
KMaxBytes = 128 * 1024 * 1024

# this binding exists because parser limits need one shared invariant
KMaxGeometry = 300_000

# this binding exists because parser limits need one shared invariant
KMaxShapes = 500_000

# this binding exists because parser limits need one shared invariant
KMaxTokens = 12_000_000

# this binding exists because parser limits need one shared invariant
KMinIntThreeTwo = -(2**31)

# this binding exists because parser limits need one shared invariant
KMaxIntThreeTwo = 2**31 - 1

# this binding exists because parser limits need one shared invariant
KTokenPattern = RegexLib.compile(rb"\S+")

# this binding exists because parser limits need one shared invariant
KIntegerPattern = RegexLib.compile(rb"[+-]?\d+")

# this binding exists because parser limits need one shared invariant
KFlagsPattern = RegexLib.compile(rb"[01]{7}")

# this binding exists because parser limits need one shared invariant
KContinuityPattern = RegexLib.compile(rb"C0|G1|C1|G2|C2|C3|CN")

# this binding exists because parser limits need one shared invariant
KIndexedPattern = RegexLib.compile(rb"([1-9]\d*)(C0|G1|C1|G2|C2|C3|CN)")

# this binding exists because parser limits need one shared invariant
KVersionLine = b"CASCADE Topology V1, (c) Matra-Datavision"

# this binding exists because parser limits need one shared invariant
KVersionLines = frozenset(
    {
        KVersionLine,
        b"CASCADE Topology V2, (c) Matra-Datavision",
        b"CASCADE Topology V3, (c) Open Cascade",
    }
)

# this binding exists because parser limits need one shared invariant
KShapeTypes = frozenset({b"Ve", b"Ed", b"Wi", b"Fa", b"Sh", b"So", b"CS", b"Co"})

# this binding exists because parser limits need one shared invariant
KShapeChildTypes: dict[bytes, frozenset[bytes]] = {
    b"Ve": frozenset(),
    b"Ed": frozenset({b"Ve"}),
    b"Wi": frozenset({b"Ed"}),
    b"Fa": frozenset({b"Wi"}),
    b"Sh": frozenset({b"Fa"}),
    b"So": frozenset({b"Sh"}),
    b"CS": frozenset({b"So"}),
    b"Co": KShapeTypes,
}

# this binding exists because parser limits need one shared invariant
KMaxRecursion = 64

# this binding exists because parser limits need one shared invariant
KMaxVertexBucket = 64

# this binding exists because parser limits need one shared invariant
KVertexDigits = 15


# this class exists because related parser state needs one focused owner
class DecodeFailure(ValueError):
    __slots__ = ()


# this class exists because token cursor state needs one focused owner
class TokenCursor:
    __slots__ = ("DataValueA", "Iterator", "Lookahead", "LastEnd", "Count")

    # this definition exists because focused parser behavior needs one stable owner
    def __init__(self, DataValue: bytes) -> None:
        self.DataValueA = DataValue
        self.Iterator = iter(KTokenPattern.finditer(DataValue))
        self.Lookahead: RegexLib.Match[bytes] | None = None
        self.LastEnd = 0
        self.Count = 0

    # this definition exists because focused parser behavior needs one stable owner
    def TakeToken(self) -> bytes:
        if self.Lookahead is None:
            try:
                MatchValue = next(self.Iterator)
            except StopIteration as ErrorValue:
                raise DecodeFailure("unexpected end of BRep data") from ErrorValue
        else:
            MatchValue = self.Lookahead
            self.Lookahead = None
        Token = MatchValue.group(0)
        self.LastEnd = MatchValue.end()
        self.Count += 1
        if self.Count > KMaxTokens or len(Token) > 128:
            raise DecodeFailure("BRep token bounds exceeded")
        return Token

    # this definition exists because focused parser behavior needs one stable owner
    def PeekToken(self) -> bytes | None:
        if self.Lookahead is None:
            try:
                self.Lookahead = next(self.Iterator)
            except StopIteration:
                return None
        return self.Lookahead.group(0)


# this class exists because line sensitive token rules need one focused owner
class TokenLines(TokenCursor):
    __slots__ = ()

    # this definition exists because focused parser behavior needs one stable owner
    def IsFaceTriNext(self) -> bool:
        CurrentEnd = self.DataValueA.find(b"\n", self.LastEnd)
        if CurrentEnd < 0:
            return False
        CurrentTail = self.DataValueA[self.LastEnd : CurrentEnd]
        if RegexLib.fullmatch(rb"[ \t]*\r?", CurrentTail) is None:
            return False
        NextStart = CurrentEnd + 1
        NextEnd = self.DataValueA.find(b"\n", NextStart)
        if NextEnd < 0:
            NextEnd = len(self.DataValueA)
        LineValue = self.DataValueA[NextStart:NextEnd]
        return RegexLib.fullmatch(rb"2[ \t]+[1-9]\d*[ \t]*\r?", LineValue) is not None

    # this definition exists because focused parser behavior needs one stable owner
    def ExpectToken(self, Expected: bytes) -> None:
        if self.TakeToken() != Expected:
            raise DecodeFailure("unexpected BRep token")


# this class exists because numeric token conversion needs one focused owner
class TokenValues(TokenCursor):
    __slots__ = ()

    # this definition exists because focused parser behavior needs one stable owner
    def ReadInteger(self, Minimum: int = 0, Maximum: int = KMaxShapes) -> int:
        Token = self.TakeToken()
        if KIntegerPattern.fullmatch(Token) is None:
            raise DecodeFailure("invalid BRep integer")
        Value = int(Token)
        if Value < Minimum or Value > Maximum:
            raise DecodeFailure("BRep integer is out of bounds")
        return Value

    # this definition exists because focused parser behavior needs one stable owner
    def SignedInteger(
        self, Minimum: int = -KMaxShapes, Maximum: int = KMaxShapes
    ) -> int:
        Token = self.TakeToken()
        if KIntegerPattern.fullmatch(Token) is None:
            raise DecodeFailure("invalid BRep integer")
        Value = int(Token)
        if Value < Minimum or Value > Maximum:
            raise DecodeFailure("BRep integer is out of bounds")
        return Value

    # this definition exists because focused parser behavior needs one stable owner
    def ReadNumber(self) -> float:
        Token = self.TakeToken()
        if len(Token) > 30:
            raise DecodeFailure("BRep number is out of bounds")
        try:
            Value = float(Token)
        except ValueError as ErrorValue:
            raise DecodeFailure("invalid BRep number") from ErrorValue
        if not IsFinite(Value):
            raise DecodeFailure("non-finite BRep number")
        return Value


# this class exists because parser consumers need one complete token interface
class Tokens(TokenLines, TokenValues):
    __slots__ = ()


# this class exists because related parser state needs one focused owner
@Dataclass(frozen=True, slots=True)
class Reference:
    Orientation: str
    RecordA: int
    KLocation: int = 0


# this class exists because related parser state needs one focused owner
@Dataclass(frozen=True, slots=True)
class VertexData:
    Tolerance: float
    Point: VectorThree


# this class exists because related parser state needs one focused owner
@Dataclass(frozen=True, slots=True)
class EdgeData:
    Tolerance: float
    Curve: int
    FirstValue: float
    LastValue: float
    KLocation: int = 0


# this class exists because related parser state needs one focused owner
@Dataclass(frozen=True, slots=True)
class FaceData:
    Natural: bool
    Tolerance: float
    Surface: int
    KLocation: int = 0


# this class exists because related parser state needs one focused owner
@Dataclass(frozen=True, slots=True)
class ShapeRecord:
    KindValue: bytes
    FlagBits: str
    Children: tuple[Reference, ...]
    GeometryA: VertexData | EdgeData | FaceData | None


# this definition exists because focused parser behavior needs one stable owner
def VectorValue(TokensA: Tokens) -> VectorThree:
    return VectorThree(TokensA.ReadNumber(), TokensA.ReadNumber(), TokensA.ReadNumber())


# this definition exists because focused parser behavior needs one stable owner
def DotValue(LeftValue: VectorThree, RightValue: VectorThree) -> float:
    return (
        LeftValue.x * RightValue.x
        + LeftValue.y * RightValue.y
        + LeftValue.z * RightValue.z
    )


# this definition exists because focused parser behavior needs one stable owner
def LengthValue(Value: VectorThree) -> float:
    return SquareRoot(DotValue(Value, Value))


# this definition exists because focused parser behavior needs one stable owner
def CrossValue(LeftValue: VectorThree, RightValue: VectorThree) -> VectorThree:
    return VectorThree(
        LeftValue.y * RightValue.z - LeftValue.z * RightValue.y,
        LeftValue.z * RightValue.x - LeftValue.x * RightValue.z,
        LeftValue.x * RightValue.y - LeftValue.y * RightValue.x,
    )


# this definition exists because focused parser behavior needs one stable owner
def IsUnit(Value: VectorThree) -> bool:
    return IsClose(LengthValue(Value), 1.0, rel_tol=1e-10, abs_tol=1e-10)


# this definition exists because focused parser behavior needs one stable owner
def IsFrame(
    Normal: VectorThree, XDirection: VectorThree, YDirection: VectorThree
) -> bool:
    ExpectedY = CrossValue(Normal, XDirection)
    Handedness = DotValue(ExpectedY, YDirection)
    return (
        IsUnit(Normal)
        and IsUnit(XDirection)
        and IsUnit(YDirection)
        and IsClose(DotValue(Normal, XDirection), 0.0, abs_tol=1e-10)
        and IsClose(DotValue(Normal, YDirection), 0.0, abs_tol=1e-10)
        and IsClose(DotValue(XDirection, YDirection), 0.0, abs_tol=1e-10)
        and IsClose(abs(Handedness), 1.0, rel_tol=1e-10, abs_tol=1e-10)
    )


# this definition exists because focused parser behavior needs one stable owner
def ReadCount(TokensA: Tokens, Label: bytes, Maximum: int) -> int:
    TokensA.ExpectToken(Label)
    return TokensA.ReadInteger(0, Maximum)


# this definition exists because focused parser behavior needs one stable owner
def ZeroTable(TokensA: Tokens, Label: bytes) -> None:
    if ReadCount(TokensA, Label, 0) != 0:
        raise DecodeFailure("unsupported BRep table")


# this definition exists because focused parser behavior needs one stable owner
def ReadReference(
    TokensA: Tokens, ShapeCount: int, LocationCount: int = 0
) -> Reference | None:
    Token = TokensA.TakeToken()
    if Token == b"*":
        return None
    if len(Token) < 2 or Token[:1] not in {b"+", b"-", b"i", b"e"}:
        raise DecodeFailure("invalid BRep shape reference")
    ReadNumber = Token[1:]
    if KIntegerPattern.fullmatch(ReadNumber) is None:
        raise DecodeFailure("invalid BRep shape reference")
    RecordA = int(ReadNumber)
    if RecordA < 1 or RecordA > ShapeCount:
        raise DecodeFailure("unsupported BRep shape location")
    LocationA = TokensA.ReadInteger(0, LocationCount)
    return Reference(Token[:1].decode("ascii"), RecordA, LocationA)


# this definition exists because focused parser behavior needs one stable owner
def IsBoolean(TokensA: Tokens) -> bool:
    return bool(TokensA.ReadInteger(0, 1))


# this definition exists because focused parser behavior needs one stable owner
def ReadNumbers(TokensA: Tokens, Count: int) -> None:
    if Count < 0 or Count > KMaxGeometry:
        raise DecodeFailure("BRep numeric record is out of bounds")
    for _ in range(Count):
        TokensA.ReadNumber()


# this definition exists because focused parser behavior needs one stable owner
def BoundedProduct(LeftValue: int, RightValue: int) -> int:
    if (
        LeftValue < 0
        or RightValue < 0
        or (LeftValue and RightValue > KMaxGeometry // LeftValue)
    ):
        raise DecodeFailure("BRep array dimensions are out of bounds")
    Value = LeftValue * RightValue
    if Value > KMaxGeometry:
        raise DecodeFailure("BRep array dimensions are out of bounds")
    return Value


# this definition exists because focused parser behavior needs one stable owner
def PositiveIndex(TokensA: Tokens, Count: int) -> int:
    if Count < 1:
        raise DecodeFailure("BRep references an empty table")
    return TokensA.ReadInteger(1, Count)


# this definition exists because focused parser behavior needs one stable owner
def LocationIndex(TokensA: Tokens, Count: int) -> int:
    return TokensA.ReadInteger(0, Count)


# this definition exists because focused parser behavior needs one stable owner
def Continuity(TokensA: Tokens) -> bytes:
    Value = TokensA.TakeToken()
    if KContinuityPattern.fullmatch(Value) is None:
        raise DecodeFailure("invalid BRep continuity")
    return Value


# this definition exists because spline curve payloads need focused bounds checks
def CurveSpline(TokensA: Tokens, Dimension: int, KindValue: int) -> None:
    Rational = IsBoolean(TokensA)
    if KindValue == 6:
        Degree = TokensA.ReadInteger(1, KMaxGeometry - 1)
        Poles = Degree + 1
        ReadNumbers(TokensA, BoundedProduct(Poles, Dimension + int(Rational)))
        return
    IsBoolean(TokensA)
    TokensA.ReadInteger(1, KMaxGeometry)
    Poles = TokensA.ReadInteger(2, KMaxGeometry)
    Knots = TokensA.ReadInteger(2, KMaxGeometry)
    ReadNumbers(TokensA, BoundedProduct(Poles, Dimension + int(Rational)))
    for _ in range(Knots):
        TokensA.ReadNumber()
        TokensA.ReadInteger(1, KMaxGeometry)


# this definition exists because focused parser behavior needs one stable owner
def CurveGeometry(TokensA: Tokens, Dimension: int, Depth: int = 0) -> None:
    if Depth > KMaxRecursion or Dimension not in {2, 3}:
        raise DecodeFailure("BRep curve recursion is out of bounds")
    KindValue = TokensA.ReadInteger(1, 9)
    FrameSize = 6 if Dimension == 2 else 12
    if KindValue == 1:
        ReadNumbers(TokensA, Dimension * 2)
    elif KindValue in {2, 4}:
        ReadNumbers(TokensA, FrameSize + 1)
    elif KindValue in {3, 5}:
        ReadNumbers(TokensA, FrameSize + 2)
    elif KindValue in {6, 7}:
        CurveSpline(TokensA, Dimension, KindValue)
    elif KindValue == 8:
        ReadNumbers(TokensA, 2)
        CurveGeometry(TokensA, Dimension, Depth + 1)
    else:
        TokensA.ReadNumber()
        if Dimension == 3:
            ReadNumbers(TokensA, 3)
        CurveGeometry(TokensA, Dimension, Depth + 1)


# this definition exists because spline surface payloads need focused bounds checks
def SurfaceSpline(TokensA: Tokens, KindValue: int) -> None:
    URational = IsBoolean(TokensA)
    VRational = IsBoolean(TokensA)
    if KindValue == 8:
        UDegree = TokensA.ReadInteger(1, KMaxGeometry - 1)
        VDegree = TokensA.ReadInteger(1, KMaxGeometry - 1)
        Poles = BoundedProduct(UDegree + 1, VDegree + 1)
        ReadNumbers(TokensA, BoundedProduct(Poles, 3 + int(URational or VRational)))
        return
    IsBoolean(TokensA)
    IsBoolean(TokensA)
    TokensA.ReadInteger(1, KMaxGeometry)
    TokensA.ReadInteger(1, KMaxGeometry)
    UPoles = TokensA.ReadInteger(2, KMaxGeometry)
    VPoles = TokensA.ReadInteger(2, KMaxGeometry)
    UKnots = TokensA.ReadInteger(2, KMaxGeometry)
    VKnots = TokensA.ReadInteger(2, KMaxGeometry)
    Poles = BoundedProduct(UPoles, VPoles)
    ReadNumbers(TokensA, BoundedProduct(Poles, 3 + int(URational or VRational)))
    for Count in (UKnots, VKnots):
        for _ in range(Count):
            TokensA.ReadNumber()
            TokensA.ReadInteger(1, KMaxGeometry)


# this definition exists because focused parser behavior needs one stable owner
def SurfaceGeometry(TokensA: Tokens, Depth: int = 0) -> None:
    if Depth > KMaxRecursion:
        raise DecodeFailure("BRep surface recursion is out of bounds")
    KindValue = TokensA.ReadInteger(1, 11)
    if KindValue == 1:
        ReadNumbers(TokensA, 12)
    elif KindValue in {2, 4}:
        ReadNumbers(TokensA, 13)
    elif KindValue in {3, 5}:
        ReadNumbers(TokensA, 14)
    elif KindValue in {6, 7}:
        ReadNumbers(TokensA, 3 if KindValue == 6 else 6)
        CurveGeometry(TokensA, 3, Depth + 1)
    elif KindValue in {8, 9}:
        SurfaceSpline(TokensA, KindValue)
    elif KindValue == 10:
        ReadNumbers(TokensA, 4)
        SurfaceGeometry(TokensA, Depth + 1)
    else:
        TokensA.ReadNumber()
        SurfaceGeometry(TokensA, Depth + 1)


# this definition exists because focused parser behavior needs one stable owner
def LocationProduct(
    LeftValue: tuple[tuple[int, int], ...], RightValue: tuple[tuple[int, int], ...]
) -> tuple[tuple[int, int], ...]:
    Result: list[tuple[int, int]] = []
    for Datum, Power in Chain(RightValue, LeftValue):
        if Result and Result[-1][0] == Datum:
            Combined = Result[-1][1] + Power
            if Combined < KMinIntThreeTwo or Combined > KMaxIntThreeTwo:
                raise DecodeFailure("BRep location power is out of bounds")
            Result.pop()
            if Combined:
                Result.append((Datum, Combined))
        else:
            Result.append((Datum, Power))
        if len(Result) > KMaxGeometry:
            raise DecodeFailure("BRep location chain is out of bounds")
    return tuple(Result)


# this definition exists because focused parser behavior needs one stable owner
def LocationPower(
    Value: tuple[tuple[int, int], ...], Power: int
) -> tuple[tuple[int, int], ...]:
    if Power == 0 or not Value:
        return ()
    if Power < 0:
        Value = tuple((Datum, -DatumPower) for Datum, DatumPower in reversed(Value))
        Power = -Power
    Result: tuple[tuple[int, int], ...] = ()
    Factor = Value
    while Power:
        if Power & 1:
            Result = LocationProduct(Result, Factor)
        Power >>= 1
        if Power:
            Factor = LocationProduct(Factor, Factor)
    return Result


# this definition exists because focused parser behavior needs one stable owner
def NormalizeVector(Value: tuple[float, float, float]) -> tuple[float, float, float]:
    Magnitude = SquareRoot(sum(Component * Component for Component in Value))
    if not IsFinite(Magnitude) or Magnitude <= FloatInfo.min:
        raise DecodeFailure("invalid BRep location transform")
    Result = (
        Value[0] / Magnitude,
        Value[1] / Magnitude,
        Value[2] / Magnitude,
    )
    if not all(IsFinite(Component) for Component in Result):
        raise DecodeFailure("invalid BRep location transform")
    return Result


# this definition exists because focused parser behavior needs one stable owner
def OrthoVectors(
    Values: tuple[tuple[float, float, float], ...],
) -> tuple[tuple[float, float, float], ...]:
    FirstValue = NormalizeVector(Values[0])
    Projection = sum(Values[1][IndexA] * FirstValue[IndexA] for IndexA in range(3))
    SecondInput = (
        Values[1][0] - Projection * FirstValue[0],
        Values[1][1] - Projection * FirstValue[1],
        Values[1][2] - Projection * FirstValue[2],
    )
    Second = NormalizeVector(SecondInput)
    FirstProjection = sum(Values[2][IndexA] * FirstValue[IndexA] for IndexA in range(3))
    SecondProjection = sum(Values[2][IndexA] * Second[IndexA] for IndexA in range(3))
    ThirdInput = (
        Values[2][0] - FirstProjection * FirstValue[0] - SecondProjection * Second[0],
        Values[2][1] - FirstProjection * FirstValue[1] - SecondProjection * Second[1],
        Values[2][2] - FirstProjection * FirstValue[2] - SecondProjection * Second[2],
    )
    Third = NormalizeVector(ThirdInput)
    return FirstValue, Second, Third


# this definition exists because focused parser behavior needs one stable owner
def ParseTransform(TokensA: Tokens) -> tuple[float, ...]:
    Values = tuple(TokensA.ReadNumber() for _ in range(12))
    Determinant = (
        Values[0] * (Values[5] * Values[10] - Values[6] * Values[9])
        - Values[1] * (Values[4] * Values[10] - Values[6] * Values[8])
        + Values[2] * (Values[4] * Values[9] - Values[5] * Values[8])
    )
    if not IsFinite(Determinant) or abs(Determinant) < FloatInfo.min:
        raise DecodeFailure("singular BRep location transform")
    Scale = abs(Determinant) ** (1.0 / 3.0)
    if Determinant < 0.0:
        Scale = -Scale
    RowsValue: tuple[tuple[float, float, float], ...] = (
        (Values[0] / Scale, Values[1] / Scale, Values[2] / Scale),
        (Values[4] / Scale, Values[5] / Scale, Values[6] / Scale),
        (Values[8] / Scale, Values[9] / Scale, Values[10] / Scale),
    )
    Columns = (
        (RowsValue[0][0], RowsValue[1][0], RowsValue[2][0]),
        (RowsValue[0][1], RowsValue[1][1], RowsValue[2][1]),
        (RowsValue[0][2], RowsValue[1][2], RowsValue[2][2]),
    )
    Columns = OrthoVectors(Columns)
    RowsValue = (
        (Columns[0][0], Columns[1][0], Columns[2][0]),
        (Columns[0][1], Columns[1][1], Columns[2][1]),
        (Columns[0][2], Columns[1][2], Columns[2][2]),
    )
    OrthoVectors(RowsValue)
    return Values


# this binding exists because parser limits need one shared invariant
KIdentityLocation = (
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
)


# this definition exists because focused parser behavior needs one stable owner
def ProductLocation(
    LeftValue: tuple[float, ...], RightValue: tuple[float, ...]
) -> tuple[float, ...]:
    Result: list[float] = []
    for RowValue in range(3):
        for Column in range(3):
            Result.append(
                sum(
                    LeftValue[RowValue * 4 + Inner] * RightValue[Inner * 4 + Column]
                    for Inner in range(3)
                )
            )
        Result.append(
            LeftValue[RowValue * 4 + 3]
            + sum(
                LeftValue[RowValue * 4 + Inner] * RightValue[Inner * 4 + 3]
                for Inner in range(3)
            )
        )
    if not all(IsFinite(Value) for Value in Result):
        raise DecodeFailure("invalid BRep location transform")
    return tuple(Result)


# this definition exists because focused parser behavior needs one stable owner
def InverseLocation(Value: tuple[float, ...]) -> tuple[float, ...]:
    (
        AValue,
        BValue,
        CValue,
        TxValue,
        DValue,
        EValue,
        FValue,
        TyValue,
        GValue,
        HValue,
        Index,
        TzValue,
    ) = Value
    Determinant = (
        AValue * (EValue * Index - FValue * HValue)
        - BValue * (DValue * Index - FValue * GValue)
        + CValue * (DValue * HValue - EValue * GValue)
    )
    if not IsFinite(Determinant) or abs(Determinant) < FloatInfo.min:
        raise DecodeFailure("singular BRep location transform")
    Inverse = (
        (EValue * Index - FValue * HValue) / Determinant,
        (CValue * HValue - BValue * Index) / Determinant,
        (BValue * FValue - CValue * EValue) / Determinant,
        0.0,
        (FValue * GValue - DValue * Index) / Determinant,
        (AValue * Index - CValue * GValue) / Determinant,
        (CValue * DValue - AValue * FValue) / Determinant,
        0.0,
        (DValue * HValue - EValue * GValue) / Determinant,
        (BValue * GValue - AValue * HValue) / Determinant,
        (AValue * EValue - BValue * DValue) / Determinant,
        0.0,
    )
    Translated = (
        *Inverse[:3],
        -(Inverse[0] * TxValue + Inverse[1] * TyValue + Inverse[2] * TzValue),
        *Inverse[4:7],
        -(Inverse[4] * TxValue + Inverse[5] * TyValue + Inverse[6] * TzValue),
        *Inverse[8:11],
        -(Inverse[8] * TxValue + Inverse[9] * TyValue + Inverse[10] * TzValue),
    )
    if not all(IsFinite(Component) for Component in Translated):
        raise DecodeFailure("invalid BRep location transform")
    return Translated


# this definition exists because focused parser behavior needs one stable owner
def MatrixPower(Value: tuple[float, ...], Power: int) -> tuple[float, ...]:
    if Power < 0:
        Value = InverseLocation(Value)
        Power = -Power
    Result = KIdentityLocation
    Factor = Value
    while Power:
        if Power & 1:
            Result = ProductLocation(Result, Factor)
        Power >>= 1
        if Power:
            Factor = ProductLocation(Factor, Factor)
    return Result


# this definition exists because focused parser behavior needs one stable owner
def ModelLocations(TokensA: Tokens) -> tuple[tuple[float, ...], ...]:
    Count = ReadCount(TokensA, b"Locations", KMaxGeometry)
    Chains: list[tuple[tuple[int, int], ...]] = []
    Direct: dict[int, tuple[float, ...]] = {}
    Matrices: list[tuple[float, ...]] = []
    UniqueLocations: set[tuple[tuple[int, int], ...]] = set()
    for IndexA in range(1, Count + 1):
        KindValue = TokensA.ReadInteger(1, 2)
        if KindValue == 1:
            Direct[IndexA] = ParseTransform(TokensA)
            LocationA = ((IndexA, 1),)
        else:
            LocationA = ()
            ReferenceA = TokensA.ReadInteger(0, len(Chains))
            while ReferenceA:
                Power = TokensA.SignedInteger()
                LocationA = LocationProduct(
                    LocationPower(Chains[ReferenceA - 1], Power), LocationA
                )
                ReferenceA = TokensA.ReadInteger(0, len(Chains))
        if not LocationA or LocationA in UniqueLocations:
            raise DecodeFailure("invalid BRep location record")
        Matrix = KIdentityLocation
        for Datum, Power in LocationA:
            BaseValue = Direct.get(Datum)
            if BaseValue is None:
                raise DecodeFailure("invalid BRep location record")
            Matrix = ProductLocation(Matrix, MatrixPower(BaseValue, Power))
        Chains.append(LocationA)
        Matrices.append(Matrix)
        UniqueLocations.add(LocationA)
    return tuple(Matrices)


# this definition exists because focused parser behavior needs one stable owner
def LocationScale(Value: tuple[float, ...]) -> float:
    Columns = tuple(
        tuple(Value[RowValue * 4 + Column] for RowValue in range(3))
        for Column in range(3)
    )
    Lengths = tuple(
        SquareRoot(sum(Component * Component for Component in ItemValue))
        for ItemValue in Columns
    )
    if (
        any(not IsFinite(Length) or Length <= FloatInfo.min for Length in Lengths)
        or not IsClose(Lengths[0], Lengths[1], rel_tol=1e-10, abs_tol=1e-12)
        or not IsClose(Lengths[0], Lengths[2], rel_tol=1e-10, abs_tol=1e-12)
        or any(
            not IsClose(
                sum(LeftValue[IndexA] * RightValue[IndexA] for IndexA in range(3)),
                0.0,
                rel_tol=0.0,
                abs_tol=1e-10 * Lengths[0] * Lengths[0],
            )
            for LeftValue, RightValue in (
                (Columns[0], Columns[1]),
                (Columns[0], Columns[2]),
                (Columns[1], Columns[2]),
            )
        )
    ):
        raise DecodeFailure("unsupported BRep location transform")
    Determinant = (
        Value[0] * (Value[5] * Value[10] - Value[6] * Value[9])
        - Value[1] * (Value[4] * Value[10] - Value[6] * Value[8])
        + Value[2] * (Value[4] * Value[9] - Value[5] * Value[8])
    )
    if Determinant <= 0.0:
        raise DecodeFailure("unsupported BRep location transform")
    return Lengths[0]


# this definition exists because focused parser behavior needs one stable owner
def LocationPoint(Value: tuple[float, ...], Point: VectorThree) -> VectorThree:
    Components = (Point.x, Point.y, Point.z)
    return VectorThree(
        *(
            Value[RowValue * 4 + 3]
            + sum(
                Value[RowValue * 4 + Column] * Components[Column] for Column in range(3)
            )
            for RowValue in range(3)
        )
    )


# this definition exists because focused parser behavior needs one stable owner
def ApplyDirection(Value: tuple[float, ...], Direction: VectorThree) -> VectorThree:
    Components = (Direction.x, Direction.y, Direction.z)
    Transformed = (
        sum(Value[Column] * Components[Column] for Column in range(3)),
        sum(Value[4 + Column] * Components[Column] for Column in range(3)),
        sum(Value[8 + Column] * Components[Column] for Column in range(3)),
    )
    Normalized = NormalizeVector(Transformed)
    return VectorThree(*Normalized)


# this definition exists because focused parser behavior needs one stable owner
def LocatedInputs(
    CurvesA: tuple[LineCurve, ...],
    SurfacesA: tuple[PlaneSurface, ...],
    RecordsA: Mapping[int, ShapeRecord],
    LocationA: tuple[float, ...],
) -> tuple[
    tuple[LineCurve, ...],
    tuple[PlaneSurface, ...],
    dict[int, ShapeRecord],
]:
    Scale = LocationScale(LocationA)
    TransformedCurves = tuple(
        LineCurve(
            Curve.id,
            LocationPoint(LocationA, Curve.origin),
            ApplyDirection(LocationA, Curve.direction),
            provenance=Curve.provenance,
            attributes=Curve.attributes,
        )
        for Curve in CurvesA
    )
    TransformedSurfaces = tuple(
        PlaneSurface(
            Surface.id,
            LocationPoint(LocationA, Surface.origin),
            ApplyDirection(LocationA, Surface.normal),
            ApplyDirection(LocationA, Surface.reference_direction),
            provenance=Surface.provenance,
            attributes=Surface.attributes,
        )
        for Surface in SurfacesA
    )
    TransformedRecords: dict[int, ShapeRecord] = {}
    for ReadNumber, RecordA in RecordsA.items():
        GeometryA = RecordA.GeometryA
        if isinstance(GeometryA, VertexData):
            GeometryA = VertexData(
                GeometryA.Tolerance * Scale,
                LocationPoint(LocationA, GeometryA.Point),
            )
        elif isinstance(GeometryA, EdgeData):
            GeometryA = EdgeData(
                GeometryA.Tolerance * Scale,
                GeometryA.Curve,
                GeometryA.FirstValue * Scale,
                GeometryA.LastValue * Scale,
            )
        elif isinstance(GeometryA, FaceData):
            GeometryA = FaceData(
                GeometryA.Natural,
                GeometryA.Tolerance * Scale,
                GeometryA.Surface,
            )
        TransformedRecords[ReadNumber] = ShapeRecord(
            RecordA.KindValue,
            RecordA.FlagBits,
            RecordA.Children,
            GeometryA,
        )
    return TransformedCurves, TransformedSurfaces, TransformedRecords


# this definition exists because focused parser behavior needs one stable owner
def ReadLocations(TokensA: Tokens) -> int:
    Count = ReadCount(TokensA, b"Locations", KMaxGeometry)
    LocationsA: list[tuple[tuple[int, int], ...]] = []
    UniqueLocations: set[tuple[tuple[int, int], ...]] = set()
    for IndexA in range(1, Count + 1):
        KindValue = TokensA.ReadInteger(1, 2)
        if KindValue == 1:
            ParseTransform(TokensA)
            LocationA = ((IndexA, 1),)
        else:
            LocationA = ()
            ReferenceA = TokensA.ReadInteger(0, len(LocationsA))
            while ReferenceA:
                Power = TokensA.SignedInteger()
                LocationA = LocationProduct(
                    LocationPower(LocationsA[ReferenceA - 1], Power), LocationA
                )
                ReferenceA = TokensA.ReadInteger(0, len(LocationsA))
        if not LocationA or LocationA in UniqueLocations:
            raise DecodeFailure("invalid BRep location record")
        LocationsA.append(LocationA)
        UniqueLocations.add(LocationA)
    return Count


# this definition exists because focused parser behavior needs one stable owner
def ReadCurves(TokensA: Tokens, Label: bytes, Dimension: int) -> int:
    Count = ReadCount(TokensA, Label, KMaxGeometry)
    for _ in range(Count):
        CurveGeometry(TokensA, Dimension)
    return Count


# this definition exists because focused parser behavior needs one stable owner
def PolygonThree(TokensA: Tokens) -> int:
    Count = ReadCount(TokensA, b"Polygon3D", KMaxGeometry)
    for _ in range(Count):
        Nodes = TokensA.ReadInteger(1, KMaxGeometry)
        Parameters = IsBoolean(TokensA)
        if TokensA.ReadNumber() < 0.0:
            raise DecodeFailure("negative BRep polygon deflection")
        ReadNumbers(TokensA, BoundedProduct(Nodes, 3))
        if Parameters:
            ReadNumbers(TokensA, Nodes)
    return Count


# this definition exists because focused parser behavior needs one stable owner
def TriPolygons(TokensA: Tokens) -> tuple[int, ...]:
    Count = ReadCount(TokensA, b"PolygonOnTriangulations", KMaxGeometry)
    MaximumNodes: list[int] = []
    for _ in range(Count):
        Nodes = TokensA.ReadInteger(1, KMaxGeometry)
        MaximumNode = 0
        for _ in range(Nodes):
            MaximumNode = max(MaximumNode, TokensA.ReadInteger(1, KMaxGeometry))
        MaximumNodes.append(MaximumNode)
        TokensA.ExpectToken(b"p")
        if TokensA.ReadNumber() < 0.0:
            raise DecodeFailure("negative BRep polygon deflection")
        if IsBoolean(TokensA):
            ReadNumbers(TokensA, Nodes)
    return tuple(MaximumNodes)


# this definition exists because focused parser behavior needs one stable owner
def ReadSurfaces(TokensA: Tokens) -> int:
    Count = ReadCount(TokensA, b"Surfaces", KMaxGeometry)
    for _ in range(Count):
        SurfaceGeometry(TokensA)
    return Count


# this definition exists because focused parser behavior needs one stable owner
def Triangulations(TokensA: Tokens) -> tuple[int, ...]:
    Count = ReadCount(TokensA, b"Triangulations", KMaxGeometry)
    NodeCounts: list[int] = []
    for _ in range(Count):
        Nodes = TokensA.ReadInteger(1, KMaxGeometry)
        NodeCounts.append(Nodes)
        Triangles = TokensA.ReadInteger(1, KMaxGeometry)
        Parameters = IsBoolean(TokensA)
        if TokensA.ReadNumber() < 0.0:
            raise DecodeFailure("negative BRep triangulation deflection")
        ReadNumbers(TokensA, BoundedProduct(Nodes, 3))
        if Parameters:
            ReadNumbers(TokensA, BoundedProduct(Nodes, 2))
        for _ in range(BoundedProduct(Triangles, 3)):
            TokensA.ReadInteger(1, Nodes)
    return tuple(NodeCounts)


# this definition exists because focused parser behavior needs one stable owner
def VertexStructure(
    TokensA: Tokens,
    LocationsA: int,
    CurvesTwoD: int,
    CurvesThreeD: int,
    SurfacesA: int,
) -> None:
    if TokensA.ReadNumber() < 0.0:
        raise DecodeFailure("negative BRep vertex tolerance")
    ReadNumbers(TokensA, 3)
    while True:
        Parameter = TokensA.ReadNumber()
        KindValue = TokensA.ReadInteger(0, 3)
        if KindValue == 0:
            if Parameter != 0.0:
                raise DecodeFailure("invalid BRep vertex terminator")
            return
        if KindValue == 1:
            PositiveIndex(TokensA, CurvesThreeD)
        elif KindValue == 2:
            PositiveIndex(TokensA, CurvesTwoD)
            PositiveIndex(TokensA, SurfacesA)
        else:
            TokensA.ReadNumber()
            PositiveIndex(TokensA, SurfacesA)
        LocationIndex(TokensA, LocationsA)


# this definition exists because focused parser behavior needs one stable owner
def IndexContinuity(TokensA: Tokens, Count: int) -> None:
    Value = TokensA.TakeToken()
    MatchValue = KIndexedPattern.fullmatch(Value)
    if MatchValue is not None:
        IndexA = int(MatchValue.group(1))
        if IndexA < 1 or IndexA > Count:
            raise DecodeFailure("BRep curve index is out of bounds")
        return
    if KIntegerPattern.fullmatch(Value) is None:
        raise DecodeFailure("invalid BRep indexed continuity")
    IndexA = int(Value)
    if IndexA < 1 or IndexA > Count:
        raise DecodeFailure("BRep curve index is out of bounds")
    Continuity(TokensA)


# this definition exists because curve edge representations need focused validation
def EdgeCurveRep(
    TokensA: Tokens,
    KindValue: int,
    LocationsA: int,
    CurvesTwoD: int,
    CurvesThreeD: int,
    SurfacesA: int,
) -> None:
    if KindValue == 1:
        PositiveIndex(TokensA, CurvesThreeD)
        LocationIndex(TokensA, LocationsA)
        ReadNumbers(TokensA, 2)
    elif KindValue == 2:
        PositiveIndex(TokensA, CurvesTwoD)
        PositiveIndex(TokensA, SurfacesA)
        LocationIndex(TokensA, LocationsA)
        ReadNumbers(TokensA, 2)
    elif KindValue == 3:
        PositiveIndex(TokensA, CurvesTwoD)
        IndexContinuity(TokensA, CurvesTwoD)
        PositiveIndex(TokensA, SurfacesA)
        LocationIndex(TokensA, LocationsA)
        ReadNumbers(TokensA, 2)
    else:
        Continuity(TokensA)
        PositiveIndex(TokensA, SurfacesA)
        LocationIndex(TokensA, LocationsA)
        PositiveIndex(TokensA, SurfacesA)
        LocationIndex(TokensA, LocationsA)


# this definition exists because polygon edge representations need focused validation
def EdgePolygonRep(
    TokensA: Tokens,
    KindValue: int,
    LocationsA: int,
    PolygonsThreeD: int,
    PolygonsOnTriangulations: tuple[int, ...],
    TriangulationsA: tuple[int, ...],
) -> None:
    if KindValue == 5:
        PositiveIndex(TokensA, PolygonsThreeD)
        LocationIndex(TokensA, LocationsA)
        return
    PolygonIndexes = [PositiveIndex(TokensA, len(PolygonsOnTriangulations))]
    if KindValue == 7:
        PolygonIndexes.append(PositiveIndex(TokensA, len(PolygonsOnTriangulations)))
    Triangulation = PositiveIndex(TokensA, len(TriangulationsA))
    if max(PolygonsOnTriangulations[IndexA - 1] for IndexA in PolygonIndexes) > (
        TriangulationsA[Triangulation - 1]
    ):
        raise DecodeFailure("BRep polygon node is out of bounds")
    LocationIndex(TokensA, LocationsA)


# this definition exists because focused parser behavior needs one stable owner
def EdgeStructure(
    TokensA: Tokens,
    LocationsA: int,
    CurvesTwoD: int,
    CurvesThreeD: int,
    PolygonsThreeD: int,
    PolygonsOnTriangulations: tuple[int, ...],
    SurfacesA: int,
    TriangulationsA: tuple[int, ...],
) -> None:
    if TokensA.ReadNumber() < 0.0:
        raise DecodeFailure("negative BRep edge tolerance")
    IsBoolean(TokensA)
    IsBoolean(TokensA)
    IsBoolean(TokensA)
    while True:
        KindValue = TokensA.ReadInteger(0, 7)
        if KindValue == 0:
            return
        if KindValue <= 4:
            EdgeCurveRep(
                TokensA,
                KindValue,
                LocationsA,
                CurvesTwoD,
                CurvesThreeD,
                SurfacesA,
            )
        else:
            EdgePolygonRep(
                TokensA,
                KindValue,
                LocationsA,
                PolygonsThreeD,
                PolygonsOnTriangulations,
                TriangulationsA,
            )


# this definition exists because focused parser behavior needs one stable owner
def FaceStructure(
    TokensA: Tokens,
    LocationsA: int,
    SurfacesA: int,
    TriangulationsA: tuple[int, ...],
) -> None:
    KindValue = TokensA.ReadInteger(0, 2)
    if KindValue in {0, 1}:
        if TokensA.ReadNumber() < 0.0:
            raise DecodeFailure("negative BRep face tolerance")
        Surface = TokensA.ReadInteger(0, SurfacesA)
        LocationIndex(TokensA, LocationsA)
        HasTriangulation = False
        if TokensA.IsFaceTriNext():
            TokensA.ExpectToken(b"2")
            PositiveIndex(TokensA, len(TriangulationsA))
            HasTriangulation = True
        if Surface == 0 and not HasTriangulation:
            raise DecodeFailure("BRep face has no geometry")
    else:
        PositiveIndex(TokensA, len(TriangulationsA))


# this definition exists because focused parser behavior needs one stable owner
def StructureRef(
    TokensA: Tokens, ShapeCount: int, LocationCount: int
) -> tuple[Reference, int] | None:
    Token = TokensA.TakeToken()
    if Token == b"*":
        return None
    if len(Token) < 2 or Token[:1] not in {b"+", b"-", b"i", b"e"}:
        raise DecodeFailure("invalid BRep shape reference")
    ReadNumber = Token[1:]
    if KIntegerPattern.fullmatch(ReadNumber) is None:
        raise DecodeFailure("invalid BRep shape reference")
    RecordA = int(ReadNumber)
    if RecordA < 1 or RecordA > ShapeCount:
        raise DecodeFailure("BRep shape reference is out of bounds")
    LocationA = LocationIndex(TokensA, LocationCount)
    return Reference(Token[:1].decode("ascii"), RecordA), LocationA


# this definition exists because structural geometry dispatch needs one focused owner
def ReadStructGeom(
    TokensA: Tokens,
    KindValue: bytes,
    LocationsA: int,
    CurvesTwoD: int,
    CurvesThreeD: int,
    PolygonsThreeD: int,
    PolygonsOnTriangulations: tuple[int, ...],
    SurfacesA: int,
    TriangulationsA: tuple[int, ...],
) -> None:
    if KindValue == b"Ve":
        VertexStructure(TokensA, LocationsA, CurvesTwoD, CurvesThreeD, SurfacesA)
    elif KindValue == b"Ed":
        EdgeStructure(
            TokensA,
            LocationsA,
            CurvesTwoD,
            CurvesThreeD,
            PolygonsThreeD,
            PolygonsOnTriangulations,
            SurfacesA,
            TriangulationsA,
        )
    elif KindValue == b"Fa":
        FaceStructure(TokensA, LocationsA, SurfacesA, TriangulationsA)


# this definition exists because child topology validation needs one focused owner
def ReadStructKids(
    TokensA: Tokens,
    Count: int,
    LocationsA: int,
    RecordA: int,
    KindValue: bytes,
    Kinds: Mapping[int, bytes],
) -> tuple[int, ...]:
    ChildRecords: list[int] = []
    while True:
        Child = StructureRef(TokensA, Count, LocationsA)
        if Child is None:
            return tuple(ChildRecords)
        ReferenceA, _ = Child
        if ReferenceA.RecordA <= RecordA:
            raise DecodeFailure("BRep topology is not ordered bottom-up")
        ChildKind = Kinds.get(ReferenceA.RecordA)
        if ChildKind not in KShapeChildTypes[KindValue]:
            raise DecodeFailure("invalid BRep child shape type")
        ChildRecords.append(ReferenceA.RecordA)


# this definition exists because reachability validation needs one focused owner
def AssertReachable(
    RootRecord: int,
    Children: Mapping[int, tuple[int, ...]],
    Kinds: Mapping[int, bytes],
) -> None:
    Reachable: set[int] = set()
    Pending = [RootRecord]
    while Pending:
        RecordA = Pending.pop()
        if RecordA in Reachable:
            continue
        Reachable.add(RecordA)
        Pending.extend(Children[RecordA])
    if Reachable != set(Kinds):
        raise DecodeFailure("unreachable BRep topology")


# this definition exists because focused parser behavior needs one stable owner
def ShapeStructure(
    TokensA: Tokens,
    LocationsA: int,
    CurvesTwoD: int,
    CurvesThreeD: int,
    PolygonsThreeD: int,
    PolygonsOnTriangulations: tuple[int, ...],
    SurfacesA: int,
    TriangulationsA: tuple[int, ...],
) -> None:
    Count = ReadCount(TokensA, b"TShapes", KMaxShapes)
    if Count == 0:
        raise DecodeFailure("empty BRep topology")
    Kinds: dict[int, bytes] = {}
    Children: dict[int, tuple[int, ...]] = {}
    for Ordinal in range(1, Count + 1):
        KindValue = TokensA.TakeToken()
        if KindValue not in KShapeTypes:
            raise DecodeFailure("unsupported BRep shape type")
        RecordA = Count - Ordinal + 1
        ReadStructGeom(
            TokensA,
            KindValue,
            LocationsA,
            CurvesTwoD,
            CurvesThreeD,
            PolygonsThreeD,
            PolygonsOnTriangulations,
            SurfacesA,
            TriangulationsA,
        )
        FlagBits = TokensA.TakeToken()
        if KFlagsPattern.fullmatch(FlagBits) is None:
            raise DecodeFailure("invalid BRep shape flags")
        Kinds[RecordA] = KindValue
        Children[RecordA] = ReadStructKids(
            TokensA, Count, LocationsA, RecordA, KindValue, Kinds
        )
    RootValue = StructureRef(TokensA, Count, LocationsA)
    if (
        RootValue is None
        or RootValue[0].RecordA != 1
        or RootValue[0].RecordA not in Kinds
        or TokensA.PeekToken() is not None
    ):
        raise DecodeFailure("invalid BRep root shape")
    AssertReachable(RootValue[0].RecordA, Children, Kinds)


# this definition exists because focused parser behavior needs one stable owner
def VertexGeometry(TokensA: Tokens) -> VertexData:
    Tolerance = TokensA.ReadNumber()
    Point = VectorValue(TokensA)
    if Tolerance < 0.0:
        raise DecodeFailure("invalid BRep vertex tolerance")
    while True:
        Parameter = TokensA.ReadNumber()
        Representation = TokensA.ReadInteger(0, 3)
        if Representation == 0:
            if Parameter != 0.0:
                raise DecodeFailure("invalid BRep vertex representation terminator")
            break
        if Representation == 1:
            TokensA.ReadInteger(1, KMaxGeometry)
        elif Representation == 2:
            TokensA.ReadInteger(1, KMaxGeometry)
            TokensA.ReadInteger(1, KMaxGeometry)
        else:
            TokensA.ReadNumber()
            TokensA.ReadInteger(1, KMaxGeometry)
        if TokensA.ReadInteger(0, 0) != 0:
            raise DecodeFailure("unsupported BRep vertex location")
    return VertexData(Tolerance, Point)


# this definition exists because edge representation parsing needs one focused owner
def ReadEdgeReps(
    TokensA: Tokens,
    CurveCount: int,
    CurveTwoDCount: int,
    SurfaceCount: int,
    LocationCount: int,
) -> list[tuple[int, float, float, int]]:
    Representations: list[tuple[int, float, float, int]] = []
    while True:
        Representation = TokensA.ReadInteger(0, 7)
        if Representation == 0:
            return Representations
        if Representation == 1:
            Curve = TokensA.ReadInteger(1, CurveCount)
            LocationA = LocationIndex(TokensA, LocationCount)
            Representations.append(
                (Curve, TokensA.ReadNumber(), TokensA.ReadNumber(), LocationA)
            )
        elif Representation == 2:
            TokensA.ReadInteger(1, CurveTwoDCount)
            TokensA.ReadInteger(1, SurfaceCount)
            LocationIndex(TokensA, LocationCount)
            TokensA.ReadNumber()
            TokensA.ReadNumber()
        elif Representation == 3:
            TokensA.ReadInteger(1, CurveTwoDCount)
            IndexContinuity(TokensA, CurveTwoDCount)
            TokensA.ReadInteger(1, SurfaceCount)
            LocationIndex(TokensA, LocationCount)
            TokensA.ReadNumber()
            TokensA.ReadNumber()
        else:
            raise DecodeFailure("unsupported BRep edge representation")


# this definition exists because focused parser behavior needs one stable owner
def EdgeGeometry(
    TokensA: Tokens,
    CurveCount: int,
    CurveTwoDCount: int,
    SurfaceCount: int,
    LocationCount: int,
) -> EdgeData:
    Tolerance = TokensA.ReadNumber()
    TokensA.ReadInteger(0, 1)
    TokensA.ReadInteger(0, 1)
    Degenerate = TokensA.ReadInteger(0, 1)
    if Tolerance < 0.0 or Degenerate:
        raise DecodeFailure("unsupported BRep edge state")
    Representations = ReadEdgeReps(
        TokensA, CurveCount, CurveTwoDCount, SurfaceCount, LocationCount
    )
    if len(Representations) != 1:
        raise DecodeFailure("ambiguous BRep edge geometry")
    Curve, FirstValue, LastValue, LocationA = Representations[0]
    return EdgeData(Tolerance, Curve, FirstValue, LastValue, LocationA)


# this definition exists because focused parser behavior needs one stable owner
def FaceGeometry(TokensA: Tokens, SurfaceCount: int, LocationCount: int) -> FaceData:
    Natural = TokensA.ReadInteger(0, 1)
    Tolerance = TokensA.ReadNumber()
    Surface = TokensA.ReadInteger(1, SurfaceCount)
    LocationA = LocationIndex(TokensA, LocationCount)
    if Tolerance < 0.0:
        raise DecodeFailure("unsupported BRep face geometry")
    return FaceData(bool(Natural), Tolerance, Surface, LocationA)


# this definition exists because focused parser behavior needs one stable owner
def ShapeRecords(
    TokensA: Tokens,
    ShapeCount: int,
    CurveCount: int,
    CurveTwoDCount: int,
    SurfaceCount: int,
    LocationCount: int = 0,
) -> dict[int, ShapeRecord]:
    RecordsA: dict[int, ShapeRecord] = {}
    for Ordinal in range(1, ShapeCount + 1):
        KindValue = TokensA.TakeToken()
        if KindValue not in KShapeTypes:
            raise DecodeFailure("unsupported BRep shape type")
        GeometryA: VertexData | EdgeData | FaceData | None = None
        if KindValue == b"Ve":
            GeometryA = VertexGeometry(TokensA)
        elif KindValue == b"Ed":
            GeometryA = EdgeGeometry(
                TokensA,
                CurveCount,
                CurveTwoDCount,
                SurfaceCount,
                LocationCount,
            )
        elif KindValue == b"Fa":
            GeometryA = FaceGeometry(TokensA, SurfaceCount, LocationCount)
        FlagToken = TokensA.TakeToken()
        if KFlagsPattern.fullmatch(FlagToken) is None:
            raise DecodeFailure("invalid BRep shape flags")
        Children: list[Reference] = []
        while True:
            Child = ReadReference(TokensA, ShapeCount, LocationCount)
            if Child is None:
                break
            Children.append(Child)
        RecordNumber = ShapeCount - Ordinal + 1
        if any(Child.RecordA <= RecordNumber for Child in Children):
            raise DecodeFailure("BRep topology is not ordered bottom-up")
        RecordsA[RecordNumber] = ShapeRecord(
            KindValue,
            FlagToken.decode("ascii"),
            tuple(Children),
            GeometryA,
        )
    return RecordsA


# this class exists because located geometry caches need one explicit owner
@Dataclass(slots=True)
class PlacementState:
    Curves: tuple[BrepCurve, ...]
    Surfaces: tuple[BrepSurface, ...]
    Records: Mapping[int, ShapeRecord]
    Locations: tuple[tuple[float, ...], ...]
    NamePrefix: str
    PlacedCurves: list[BrepCurve]
    PlacedSurfaces: list[BrepSurface]
    PlacedRecords: dict[int, ShapeRecord]
    RecordCache: dict[tuple[int, tuple[float, ...]], int]
    CurveCache: dict[tuple[int, tuple[float, ...]], int]
    SurfaceCache: dict[tuple[int, tuple[float, ...]], int]


# this definition exists because location work should be skipped when absent
def HasLocations(Records: Mapping[int, ShapeRecord], RootRef: Reference) -> bool:
    return bool(
        RootRef.KLocation
        or any(
            ChildRef.KLocation
            for Record in Records.values()
            for ChildRef in Record.Children
        )
        or any(
            isinstance(Record.GeometryA, (EdgeData, FaceData))
            and Record.GeometryA.KLocation
            for Record in Records.values()
        )
    )


# this definition exists because curve placement and caching need one owner
def PlaceCurveMut(
    State: PlacementState, CurveIndex: int, Location: tuple[float, ...]
) -> int:
    CurveKey = (CurveIndex, Location)
    CachedIndex = State.CurveCache.get(CurveKey)
    if CachedIndex is not None:
        return CachedIndex
    BaseCurve = State.Curves[CurveIndex - 1]
    PlacedIndex = len(State.PlacedCurves) + 1
    if isinstance(BaseCurve, LineCurve):
        PlacedCurve: BrepCurve = LineCurve(
            f"{State.NamePrefix}:curve:{PlacedIndex}",
            LocationPoint(Location, BaseCurve.origin),
            ApplyDirection(Location, BaseCurve.direction),
            provenance=BaseCurve.provenance,
            attributes=BaseCurve.attributes,
        )
    elif isinstance(BaseCurve, CircleCurve):
        PlacedCurve = CircleCurve(
            f"{State.NamePrefix}:curve:{PlacedIndex}",
            LocationPoint(Location, BaseCurve.center),
            ApplyDirection(Location, BaseCurve.axis),
            ApplyDirection(Location, BaseCurve.reference_direction),
            BaseCurve.radius * LocationScale(Location),
            provenance=BaseCurve.provenance,
            attributes=BaseCurve.attributes,
        )
    else:
        raise DecodeFailure("unsupported located BRep curve")
    State.PlacedCurves.append(PlacedCurve)
    State.CurveCache[CurveKey] = PlacedIndex
    return PlacedIndex


# this definition exists because surface placement and caching need one owner
def PlaceSurfaceMut(
    State: PlacementState, SurfaceIndex: int, Location: tuple[float, ...]
) -> int:
    SurfaceKey = (SurfaceIndex, Location)
    CachedIndex = State.SurfaceCache.get(SurfaceKey)
    if CachedIndex is not None:
        return CachedIndex
    BaseSurface = State.Surfaces[SurfaceIndex - 1]
    PlacedIndex = len(State.PlacedSurfaces) + 1
    if isinstance(BaseSurface, PlaneSurface):
        PlacedSurface: BrepSurface = PlaneSurface(
            f"{State.NamePrefix}:surface:{PlacedIndex}",
            LocationPoint(Location, BaseSurface.origin),
            ApplyDirection(Location, BaseSurface.normal),
            ApplyDirection(Location, BaseSurface.reference_direction),
            provenance=BaseSurface.provenance,
            attributes=BaseSurface.attributes,
        )
    elif isinstance(BaseSurface, CylinderSurface):
        PlacedSurface = CylinderSurface(
            f"{State.NamePrefix}:surface:{PlacedIndex}",
            LocationPoint(Location, BaseSurface.origin),
            ApplyDirection(Location, BaseSurface.axis),
            ApplyDirection(Location, BaseSurface.reference_direction),
            BaseSurface.radius * LocationScale(Location),
            provenance=BaseSurface.provenance,
            attributes=BaseSurface.attributes,
        )
    else:
        raise DecodeFailure("unsupported located BRep surface")
    State.PlacedSurfaces.append(PlacedSurface)
    State.SurfaceCache[SurfaceKey] = PlacedIndex
    return PlacedIndex


# this definition exists because child placement recursion needs one owner
def PlaceChildren(
    State: PlacementState, SourceRecord: ShapeRecord, Location: tuple[float, ...]
) -> tuple[Reference, ...]:
    ChildRefs: list[Reference] = []
    for ChildRef in SourceRecord.Children:
        ChildLoc = (
            KIdentityLocation
            if not ChildRef.KLocation
            else State.Locations[ChildRef.KLocation - 1]
        )
        ChildMatrix = ProductLocation(ChildLoc, Location)
        ChildRecord = PlaceRecordMut(State, ChildRef.RecordA, ChildMatrix)
        ChildRefs.append(Reference(ChildRef.Orientation, ChildRecord))
    return tuple(ChildRefs)


# this definition exists because located topology geometry needs one transformer
def PlaceGeometry(
    State: PlacementState, SourceRecord: ShapeRecord, Location: tuple[float, ...]
) -> VertexData | EdgeData | FaceData | None:
    ScaleValue = LocationScale(Location)
    Geometry = SourceRecord.GeometryA
    if isinstance(Geometry, VertexData):
        return VertexData(
            Geometry.Tolerance * ScaleValue,
            LocationPoint(Location, Geometry.Point),
        )
    if isinstance(Geometry, EdgeData):
        SourceCurve = State.Curves[Geometry.Curve - 1]
        GeometryLoc = (
            KIdentityLocation
            if not Geometry.KLocation
            else State.Locations[Geometry.KLocation - 1]
        )
        CurveLoc = ProductLocation(GeometryLoc, Location)
        ParameterScale = (
            LocationScale(CurveLoc) if isinstance(SourceCurve, LineCurve) else 1.0
        )
        return EdgeData(
            Geometry.Tolerance * ScaleValue,
            PlaceCurveMut(State, Geometry.Curve, CurveLoc),
            Geometry.FirstValue * ParameterScale,
            Geometry.LastValue * ParameterScale,
        )
    if isinstance(Geometry, FaceData):
        GeometryLoc = (
            KIdentityLocation
            if not Geometry.KLocation
            else State.Locations[Geometry.KLocation - 1]
        )
        return FaceData(
            Geometry.Natural,
            Geometry.Tolerance * ScaleValue,
            PlaceSurfaceMut(
                State, Geometry.Surface, ProductLocation(GeometryLoc, Location)
            ),
        )
    return Geometry


# this definition exists because record placement and caching need one owner
def PlaceRecordMut(
    State: PlacementState, RecordIndex: int, Location: tuple[float, ...]
) -> int:
    RecordKey = (RecordIndex, Location)
    CachedIndex = State.RecordCache.get(RecordKey)
    if CachedIndex is not None:
        return CachedIndex
    if len(State.PlacedRecords) >= KMaxShapes:
        raise DecodeFailure("located BRep topology exceeds shape bounds")
    SourceRecord = State.Records[RecordIndex]
    ChildRefs = PlaceChildren(State, SourceRecord, Location)
    Geometry = PlaceGeometry(State, SourceRecord, Location)
    PlacedIndex = len(State.PlacedRecords) + 1
    State.PlacedRecords[PlacedIndex] = ShapeRecord(
        SourceRecord.KindValue,
        SourceRecord.FlagBits,
        ChildRefs,
        Geometry,
    )
    State.RecordCache[RecordKey] = PlacedIndex
    return PlacedIndex


# this definition exists because focused parser behavior needs one stable owner
def ApplyLocations(
    Curves: tuple[BrepCurve, ...],
    Surfaces: tuple[BrepSurface, ...],
    Records: Mapping[int, ShapeRecord],
    RootRef: Reference,
    Locations: tuple[tuple[float, ...], ...],
    NamePrefix: str,
) -> tuple[
    tuple[BrepCurve, ...],
    tuple[BrepSurface, ...],
    dict[int, ShapeRecord],
    Reference,
]:
    if not HasLocations(Records, RootRef):
        return Curves, Surfaces, dict(Records), RootRef
    State = PlacementState(
        Curves,
        Surfaces,
        Records,
        Locations,
        NamePrefix,
        [],
        [],
        {},
        {},
        {},
        {},
    )
    RootLoc = (
        KIdentityLocation if not RootRef.KLocation else Locations[RootRef.KLocation - 1]
    )
    RootIndex = PlaceRecordMut(State, RootRef.RecordA, RootLoc)
    return (
        tuple(State.PlacedCurves),
        tuple(State.PlacedSurfaces),
        State.PlacedRecords,
        Reference(RootRef.Orientation, RootIndex),
    )


# this definition exists because focused parser behavior needs one stable owner
def Opposite(Orientation: str) -> str:
    if Orientation == "+":
        return "-"
    if Orientation == "-":
        return "+"
    raise DecodeFailure("unsupported BRep topology orientation")


# this definition exists because focused parser behavior needs one stable owner
def Compose(Outer: str, Inner: str) -> str:
    if Outer == "+":
        return Inner
    if Outer == "-":
        return Opposite(Inner)
    raise DecodeFailure("unsupported BRep topology orientation")


# this definition exists because focused parser behavior needs one stable owner
def CanonicalVerts(
    RecordsA: Mapping[int, ShapeRecord],
) -> dict[int, int]:
    ResultData: dict[int, int] = {}
    BucketData: dict[tuple[str, str, str], list[int]] = {}
    for NumberValue, RecordData in sorted(RecordsA.items(), reverse=True):
        if RecordData.KindValue != b"Ve":
            continue
        GeometryData = RecordData.GeometryA
        if not isinstance(GeometryData, VertexData):
            raise DecodeFailure("invalid BRep vertex topology")
        PointData = GeometryData.Point
        BucketKey = (
            format(PointData.x, f".{KVertexDigits}g"),
            format(PointData.y, f".{KVertexDigits}g"),
            format(PointData.z, f".{KVertexDigits}g"),
        )
        CandidateData = BucketData.setdefault(BucketKey, [])
        RepresentativeValue = NumberValue
        for CandidateValue in CandidateData:
            CandidateGeometry = RecordsA[CandidateValue].GeometryA
            if not isinstance(CandidateGeometry, VertexData):
                raise DecodeFailure("invalid BRep vertex topology")
            CandidatePoint = CandidateGeometry.Point
            ToleranceValue = max(
                GeometryData.Tolerance,
                CandidateGeometry.Tolerance,
            )
            if (PointData.x - CandidatePoint.x) ** 2 + (
                PointData.y - CandidatePoint.y
            ) ** 2 + (PointData.z - CandidatePoint.z) ** 2 <= ToleranceValue**2:
                RepresentativeValue = CandidateValue
                break
        else:
            if len(CandidateData) >= KMaxVertexBucket:
                raise DecodeFailure("BRep vertex equivalence bucket is too large")
            CandidateData.append(NumberValue)
        ResultData[NumberValue] = RepresentativeValue
    return ResultData


# this definition exists because focused parser behavior needs one stable owner
def OrderWireUses(
    UsesValue: list[Reference], EdgeVertices: Mapping[int, tuple[int, int]]
) -> list[Reference]:

    # this definition exists because focused parser behavior needs one stable owner
    def Endpoints(ReferenceA: Reference) -> tuple[int, int]:
        Start, EndValue = EdgeVertices[ReferenceA.RecordA]
        return (EndValue, Start) if ReferenceA.Orientation == "-" else (Start, EndValue)

    if not UsesValue:
        raise DecodeFailure("BRep wire is disconnected or open")
    Adjacency: dict[int, list[tuple[Reference, int]]] = {}
    for UseValue in reversed(UsesValue):
        StartVertex, EndVertex = Endpoints(UseValue)
        Adjacency.setdefault(StartVertex, []).append((UseValue, EndVertex))
    StartVertex = Endpoints(UsesValue[0])[0]
    VertexStack = [StartVertex]
    EdgeStack: list[Reference] = []
    Circuit: list[Reference] = []
    while VertexStack:
        Outgoing = Adjacency.get(VertexStack[-1])
        if Outgoing:
            UseValue, EndVertex = Outgoing.pop()
            EdgeStack.append(UseValue)
            VertexStack.append(EndVertex)
            continue
        VertexStack.pop()
        if EdgeStack:
            Circuit.append(EdgeStack.pop())
    Circuit.reverse()
    if (
        len(Circuit) != len(UsesValue)
        or Endpoints(Circuit[0])[0] != Endpoints(Circuit[-1])[1]
        or any(
            Endpoints(LeftUse)[1] != Endpoints(RightUse)[0]
            for LeftUse, RightUse in zip(Circuit, Circuit[1:])
        )
    ):
        raise DecodeFailure("BRep wire is disconnected or open")
    return Circuit


# this definition exists because vertex construction needs one focused stage
def BuildVertices(
    RecordsA: Mapping[int, ShapeRecord], IdPrefix: str
) -> tuple[list[BrepVertex], dict[int, str], dict[int, int]]:
    Vertices: list[BrepVertex] = []
    VertexIds: dict[int, str] = {}
    CanonicalVertexData = CanonicalVerts(RecordsA)
    for ReadNumber, RecordA in sorted(RecordsA.items(), reverse=True):
        if RecordA.KindValue != b"Ve":
            continue
        GeometryA = RecordA.GeometryA
        if not isinstance(GeometryA, VertexData) or RecordA.Children:
            raise DecodeFailure("invalid BRep vertex topology")
        Identifier = f"{IdPrefix}:vertex:{ReadNumber}"
        VertexIds[ReadNumber] = Identifier
        Vertices.append(BrepVertex(Identifier, GeometryA.Point, GeometryA.Tolerance))
    return Vertices, VertexIds, CanonicalVertexData


# this definition exists because edge construction needs one focused stage
def BuildEdges(
    RecordsA: Mapping[int, ShapeRecord],
    IdPrefix: str,
    VertexIds: Mapping[int, str],
    CanonicalVertexData: Mapping[int, int],
) -> tuple[list[BrepEdge], dict[int, str], dict[int, tuple[int, int]]]:
    Edges: list[BrepEdge] = []
    EdgeIds: dict[int, str] = {}
    EdgeVertices: dict[int, tuple[int, int]] = {}
    for ReadNumber, RecordA in sorted(RecordsA.items(), reverse=True):
        if RecordA.KindValue != b"Ed":
            continue
        GeometryA = RecordA.GeometryA
        if not isinstance(GeometryA, EdgeData) or len(RecordA.Children) != 2:
            raise DecodeFailure("invalid BRep edge topology")
        Forward = [Child for Child in RecordA.Children if Child.Orientation == "+"]
        ReversedValues = [
            Child for Child in RecordA.Children if Child.Orientation == "-"
        ]
        if len(Forward) != 1 or len(ReversedValues) != 1:
            raise DecodeFailure("ambiguous BRep edge vertices")
        if any(
            RecordsA[Child.RecordA].KindValue != b"Ve" for Child in RecordA.Children
        ):
            raise DecodeFailure("BRep edge references a non-vertex")
        Identifier = f"{IdPrefix}:edge:{ReadNumber}"
        EdgeIds[ReadNumber] = Identifier
        StartVertex = CanonicalVertexData[Forward[0].RecordA]
        EndVertex = CanonicalVertexData[ReversedValues[0].RecordA]
        EdgeVertices[ReadNumber] = (StartVertex, EndVertex)
        Edges.append(
            BrepEdge(
                Identifier,
                VertexIds[StartVertex],
                VertexIds[EndVertex],
                f"{IdPrefix}:curve:{GeometryA.Curve}",
                GeometryA.FirstValue,
                GeometryA.LastValue,
                GeometryA.Tolerance,
            )
        )
    return Edges, EdgeIds, EdgeVertices


# this definition exists because wire construction needs one focused stage
def BuildWireMut(
    ReadNumber: int,
    RecordA: ShapeRecord,
    WireIndex: int,
    WireReference: Reference,
    RecordsA: Mapping[int, ShapeRecord],
    EdgeVertices: Mapping[int, tuple[int, int]],
    EdgeIds: Mapping[int, str],
    IdPrefix: str,
    Coedges: list[BrepCoedge],
) -> tuple[str, BrepLoop]:
    if WireReference.Orientation not in {"+", "-"}:
        raise DecodeFailure("unsupported BRep wire orientation")
    WireValue = RecordsA[WireReference.RecordA]
    if WireValue.KindValue != b"Wi" or not WireValue.Children:
        raise DecodeFailure("BRep face references an invalid wire")
    UsesValue = list(WireValue.Children)
    if WireReference.Orientation == "-":
        UsesValue = [
            Reference(Opposite(UseValueA.Orientation), UseValueA.RecordA)
            for UseValueA in reversed(UsesValue)
        ]
    UsesValue = OrderWireUses(UsesValue, EdgeVertices)
    CoedgeIds: list[str] = []
    for UseIndex, UseValueA in enumerate(UsesValue, 1):
        if UseValueA.Orientation not in {"+", "-"}:
            raise DecodeFailure("unsupported BRep coedge orientation")
        if RecordsA[UseValueA.RecordA].KindValue != b"Ed":
            raise DecodeFailure("BRep wire references a non-edge")
        Suffix = (
            f"{WireIndex}:{UseIndex}" if len(RecordA.Children) > 1 else str(UseIndex)
        )
        Identifier = f"{IdPrefix}:coedge:{ReadNumber}:{Suffix}"
        Coedges.append(
            BrepCoedge(
                Identifier,
                EdgeIds[UseValueA.RecordA],
                reversed=UseValueA.Orientation == "-",
            )
        )
        CoedgeIds.append(Identifier)
    Suffix = f":{WireIndex}" if len(RecordA.Children) > 1 else ""
    LoopId = f"{IdPrefix}:loop:{ReadNumber}{Suffix}"
    return LoopId, BrepLoop(LoopId, tuple(CoedgeIds), WireIndex == 1)


# this definition exists because face construction needs one focused stage
def BuildFaces(
    RecordsA: Mapping[int, ShapeRecord],
    IdPrefix: str,
    EdgeVertices: Mapping[int, tuple[int, int]],
    EdgeIds: Mapping[int, str],
) -> tuple[list[BrepCoedge], list[BrepLoop], list[BrepFace], dict[int, str]]:
    Coedges: list[BrepCoedge] = []
    Loops: list[BrepLoop] = []
    Faces: list[BrepFace] = []
    FaceIds: dict[int, str] = {}
    for ReadNumber, RecordA in sorted(RecordsA.items(), reverse=True):
        if RecordA.KindValue != b"Fa":
            continue
        GeometryA = RecordA.GeometryA
        if not isinstance(GeometryA, FaceData) or not RecordA.Children:
            raise DecodeFailure("ambiguous BRep face boundary")
        LoopIds: list[str] = []
        for WireIndex, WireReference in enumerate(RecordA.Children, 1):
            LoopId, LoopValue = BuildWireMut(
                ReadNumber,
                RecordA,
                WireIndex,
                WireReference,
                RecordsA,
                EdgeVertices,
                EdgeIds,
                IdPrefix,
                Coedges,
            )
            Loops.append(LoopValue)
            LoopIds.append(LoopId)
        FaceId = f"{IdPrefix}:face:{ReadNumber}"
        FaceIds[ReadNumber] = FaceId
        Faces.append(
            BrepFace(
                FaceId,
                f"{IdPrefix}:surface:{GeometryA.Surface}",
                tuple(LoopIds),
                True,
                GeometryA.Tolerance,
                attributes={"natural_restriction": GeometryA.Natural},
            )
        )
    return Coedges, Loops, Faces, FaceIds


# this definition exists because shell construction needs one focused stage
def BuildShells(
    RecordsA: Mapping[int, ShapeRecord], IdPrefix: str, FaceIds: Mapping[int, str]
) -> tuple[list[BrepFaceUse], list[BrepShell], dict[int, str]]:
    FaceUses: list[BrepFaceUse] = []
    Shells: list[BrepShell] = []
    ShellIds: dict[int, str] = {}
    for ReadNumber, RecordA in sorted(RecordsA.items(), reverse=True):
        if RecordA.KindValue != b"Sh":
            continue
        if not RecordA.Children:
            raise DecodeFailure("empty BRep shell")
        UseIds: list[str] = []
        for IndexA, Child in enumerate(RecordA.Children, 1):
            if Child.Orientation not in {"+", "-"}:
                raise DecodeFailure("unsupported BRep face orientation")
            if RecordsA[Child.RecordA].KindValue != b"Fa":
                raise DecodeFailure("BRep shell references a non-face")
            Identifier = f"{IdPrefix}:face-use:{ReadNumber}:{IndexA}"
            FaceUses.append(
                BrepFaceUse(
                    Identifier,
                    FaceIds[Child.RecordA],
                    reversed=Child.Orientation == "-",
                )
            )
            UseIds.append(Identifier)
        ShellId = f"{IdPrefix}:shell:{ReadNumber}"
        ShellIds[ReadNumber] = ShellId
        Shells.append(BrepShell(ShellId, tuple(UseIds), RecordA.FlagBits[4] == "1"))
    return FaceUses, Shells, ShellIds


# this definition exists because region construction needs one focused stage
def BuildRegions(
    RecordsA: Mapping[int, ShapeRecord], IdPrefix: str, ShellIds: Mapping[int, str]
) -> tuple[list[BrepShellUse], list[BrepRegion], dict[int, str]]:
    ShellUses: list[BrepShellUse] = []
    Regions: list[BrepRegion] = []
    RegionIds: dict[int, str] = {}
    for ReadNumber, RecordA in sorted(RecordsA.items(), reverse=True):
        if RecordA.KindValue != b"So":
            continue
        if not RecordA.Children:
            raise DecodeFailure("empty BRep solid")
        UseIds: list[str] = []
        for IndexA, Child in enumerate(RecordA.Children, 1):
            if Child.Orientation not in {"+", "-"}:
                raise DecodeFailure("unsupported BRep shell orientation")
            if RecordsA[Child.RecordA].KindValue != b"Sh":
                raise DecodeFailure("BRep solid references a non-shell")
            Identifier = f"{IdPrefix}:shell-use:{ReadNumber}:{IndexA}"
            ShellUses.append(
                BrepShellUse(
                    Identifier,
                    ShellIds[Child.RecordA],
                    reversed=Child.Orientation == "-",
                )
            )
            UseIds.append(Identifier)
        RegionId = f"{IdPrefix}:region:{ReadNumber}"
        RegionIds[ReadNumber] = RegionId
        Regions.append(BrepRegion(RegionId, tuple(UseIds), True))
    return ShellUses, Regions, RegionIds


# this class exists because root topology assembly needs one explicit owner
@Dataclass(slots=True)
class RootState:
    RecordsA: Mapping[int, ShapeRecord]
    IdPrefix: str
    VertexIds: Mapping[int, str]
    FaceIds: Mapping[int, str]
    ShellIds: Mapping[int, str]
    RegionIds: Mapping[int, str]
    FaceUses: list[BrepFaceUse]
    Shells: list[BrepShell]
    ShellUses: list[BrepShellUse]
    Regions: list[BrepRegion]
    RootRegions: list[str]
    RootVertices: list[str]
    SeenValue: set[tuple[int, str]]


# this definition exists because root shell wrapping needs one focused stage
def AddRootShellMut(State: RootState, ReferenceA: Reference) -> None:
    UseId = f"{State.IdPrefix}:shell-use:root:{len(State.RootRegions) + 1}"
    State.ShellUses.append(
        BrepShellUse(
            UseId,
            State.ShellIds[ReferenceA.RecordA],
            reversed=ReferenceA.Orientation == "-",
        )
    )
    RegionId = f"{State.IdPrefix}:region:root:{len(State.RootRegions) + 1}"
    State.Regions.append(BrepRegion(RegionId, (UseId,), False))
    State.RootRegions.append(RegionId)


# this definition exists because root face wrapping needs one focused stage
def AddRootFaceMut(State: RootState, ReferenceA: Reference) -> None:
    Ordinal = len(State.RootRegions) + 1
    FaceUseId = f"{State.IdPrefix}:face-use:root:{Ordinal}"
    State.FaceUses.append(
        BrepFaceUse(
            FaceUseId,
            State.FaceIds[ReferenceA.RecordA],
            reversed=ReferenceA.Orientation == "-",
        )
    )
    ShellId = f"{State.IdPrefix}:shell:root:{Ordinal}"
    State.Shells.append(BrepShell(ShellId, (FaceUseId,), False))
    ShellUseId = f"{State.IdPrefix}:shell-use:root:{Ordinal}"
    State.ShellUses.append(BrepShellUse(ShellUseId, ShellId))
    RegionId = f"{State.IdPrefix}:region:root:{Ordinal}"
    State.Regions.append(BrepRegion(RegionId, (ShellUseId,), False))
    State.RootRegions.append(RegionId)


# this definition exists because root topology dispatch needs one focused owner
def CollectShapeMut(State: RootState, ReferenceA: Reference) -> None:
    KeyValue = (ReferenceA.RecordA, ReferenceA.Orientation)
    if KeyValue in State.SeenValue:
        raise DecodeFailure("ambiguous repeated BRep root topology")
    State.SeenValue.add(KeyValue)
    RecordA = State.RecordsA[ReferenceA.RecordA]
    if RecordA.KindValue in {b"Co", b"CS"}:
        if not RecordA.Children:
            raise DecodeFailure("empty BRep aggregate")
        for Child in RecordA.Children:
            CollectShapeMut(
                State,
                Reference(
                    Compose(ReferenceA.Orientation, Child.Orientation),
                    Child.RecordA,
                ),
            )
        return
    if RecordA.KindValue == b"So":
        if ReferenceA.Orientation != "+":
            raise DecodeFailure("unsupported reversed BRep solid")
        State.RootRegions.append(State.RegionIds[ReferenceA.RecordA])
        return
    if RecordA.KindValue == b"Sh":
        AddRootShellMut(State, ReferenceA)
        return
    if RecordA.KindValue == b"Fa" and ReferenceA.Orientation in {"+", "-"}:
        AddRootFaceMut(State, ReferenceA)
        return
    if RecordA.KindValue == b"Ve" and ReferenceA.Orientation == "+":
        State.RootVertices.append(State.VertexIds[ReferenceA.RecordA])
        return
    raise DecodeFailure("unsupported BRep root topology")


# this definition exists because model assembly and validation need one owner
def AssembleModel(
    CurvesA: tuple[BrepCurve, ...],
    SurfacesA: tuple[BrepSurface, ...],
    Vertices: list[BrepVertex],
    Edges: list[BrepEdge],
    Coedges: list[BrepCoedge],
    Loops: list[BrepLoop],
    Faces: list[BrepFace],
    State: RootState,
    DesignBodyId: str,
    Attributes: Mapping[str, object],
) -> BrepModel:
    BodyValue = BrepBody(
        f"{State.IdPrefix}:body:1",
        tuple(State.RootRegions),
        design_body_id=DesignBodyId,
        vertex_ids=tuple(State.RootVertices),
        attributes=dict(Attributes),
    )
    Result = BrepModel(
        curves=CurvesA,
        surfaces=SurfacesA,
        vertices=tuple(Vertices),
        edges=tuple(Edges),
        coedges=tuple(Coedges),
        loops=tuple(Loops),
        faces=tuple(Faces),
        face_uses=tuple(State.FaceUses),
        shells=tuple(State.Shells),
        shell_uses=tuple(State.ShellUses),
        regions=tuple(State.Regions),
        bodies=(BodyValue,),
    )
    BodyIds: frozenset[str] = frozenset({DesignBodyId}) if DesignBodyId else frozenset()
    if Result.validate(BodyIds):
        raise DecodeFailure("decoded BRep model is invalid")
    return Result


# this definition exists because focused parser behavior needs one stable owner
def BuildModel(
    CurvesA: tuple[BrepCurve, ...],
    SurfacesA: tuple[BrepSurface, ...],
    RecordsA: Mapping[int, ShapeRecord],
    RootValue: Reference,
    IdPrefix: str,
    DesignBodyId: str,
    Attributes: Mapping[str, object],
) -> BrepModel:
    Vertices, VertexIds, CanonicalVertexData = BuildVertices(RecordsA, IdPrefix)
    Edges, EdgeIds, EdgeVertices = BuildEdges(
        RecordsA, IdPrefix, VertexIds, CanonicalVertexData
    )
    Coedges, Loops, Faces, FaceIds = BuildFaces(
        RecordsA, IdPrefix, EdgeVertices, EdgeIds
    )
    FaceUses, Shells, ShellIds = BuildShells(RecordsA, IdPrefix, FaceIds)
    ShellUses, Regions, RegionIds = BuildRegions(RecordsA, IdPrefix, ShellIds)
    State = RootState(
        RecordsA,
        IdPrefix,
        VertexIds,
        FaceIds,
        ShellIds,
        RegionIds,
        FaceUses,
        Shells,
        ShellUses,
        Regions,
        [],
        [],
        set(),
    )
    CollectShapeMut(State, RootValue)
    return AssembleModel(
        CurvesA,
        SurfacesA,
        Vertices,
        Edges,
        Coedges,
        Loops,
        Faces,
        State,
        DesignBodyId,
        Attributes,
    )


# this definition exists because decoded model headers need one focused reader
def ExpectHeader(TokensA: Tokens) -> None:
    if TokensA.PeekToken() == b"DBRep_DrawableShape":
        TokensA.TakeToken()
    TokensA.ExpectToken(b"CASCADE")
    TokensA.ExpectToken(b"Topology")
    TokensA.ExpectToken(b"V1,")
    TokensA.ExpectToken(b"(c)")
    TokensA.ExpectToken(b"Matra-Datavision")


# this definition exists because decoded curves need one focused reader
def ReadModelCurves(
    TokensA: Tokens, IdPrefix: str
) -> tuple[int, tuple[BrepCurve, ...]]:
    CurveTwoDCount = ReadCurves(TokensA, b"Curve2ds", 2)
    CurveCount = ReadCount(TokensA, b"Curves", KMaxGeometry)
    CurvesA: list[BrepCurve] = []
    for IndexA in range(1, CurveCount + 1):
        KindValue = TokensA.ReadInteger(1, 9)
        if KindValue not in {1, 2}:
            raise DecodeFailure("unsupported BRep curve type")
        Origin = VectorValue(TokensA)
        AxisValue = VectorValue(TokensA)
        if KindValue == 1:
            if not IsUnit(AxisValue):
                raise DecodeFailure("invalid BRep line direction")
            CurvesA.append(
                LineCurve(
                    f"{IdPrefix}:curve:{IndexA}",
                    Origin,
                    AxisValue,
                    attributes={"opencascade_index": IndexA},
                )
            )
            continue
        XDirection = VectorValue(TokensA)
        YDirection = VectorValue(TokensA)
        Radius = TokensA.ReadNumber()
        if not IsFrame(AxisValue, XDirection, YDirection) or Radius <= 0.0:
            raise DecodeFailure("invalid BRep circle")
        CurvesA.append(
            CircleCurve(
                f"{IdPrefix}:curve:{IndexA}",
                Origin,
                AxisValue,
                XDirection,
                Radius,
                attributes={"opencascade_index": IndexA},
            )
        )
    return CurveTwoDCount, tuple(CurvesA)


# this definition exists because decoded surfaces need one focused reader
def ReadModelSurfs(TokensA: Tokens, IdPrefix: str) -> tuple[BrepSurface, ...]:
    SurfaceCount = ReadCount(TokensA, b"Surfaces", KMaxGeometry)
    SurfacesA: list[BrepSurface] = []
    for IndexA in range(1, SurfaceCount + 1):
        KindValue = TokensA.ReadInteger(1, 11)
        if KindValue not in {1, 2}:
            raise DecodeFailure("unsupported BRep surface type")
        Origin = VectorValue(TokensA)
        Normal = VectorValue(TokensA)
        XDirection = VectorValue(TokensA)
        YDirection = VectorValue(TokensA)
        if not IsFrame(Normal, XDirection, YDirection):
            raise DecodeFailure("invalid BRep surface frame")
        Properties = {
            "opencascade_index": IndexA,
            "reference_y": (YDirection.x, YDirection.y, YDirection.z),
        }
        if KindValue == 1:
            SurfacesA.append(
                PlaneSurface(
                    f"{IdPrefix}:surface:{IndexA}",
                    Origin,
                    Normal,
                    XDirection,
                    attributes=Properties,
                )
            )
            continue
        Radius = TokensA.ReadNumber()
        if Radius <= 0.0:
            raise DecodeFailure("invalid BRep cylinder")
        SurfacesA.append(
            CylinderSurface(
                f"{IdPrefix}:surface:{IndexA}",
                Origin,
                Normal,
                XDirection,
                Radius,
                attributes=Properties,
            )
        )
    return tuple(SurfacesA)


# this definition exists because payload decoding needs one orchestration boundary
def DecodePayload(
    DataValue: bytes,
    IdPrefix: str,
    DesignBodyId: str,
    Attributes: Mapping[str, object],
) -> BrepModel:
    TokensA = Tokens(DataValue)
    ExpectHeader(TokensA)
    LocationsA = ModelLocations(TokensA)
    CurveTwoDCount, CurvesA = ReadModelCurves(TokensA, IdPrefix)
    ZeroTable(TokensA, b"Polygon3D")
    ZeroTable(TokensA, b"PolygonOnTriangulations")
    SurfacesA = ReadModelSurfs(TokensA, IdPrefix)
    ZeroTable(TokensA, b"Triangulations")
    ShapeCount = ReadCount(TokensA, b"TShapes", KMaxShapes)
    if ShapeCount == 0:
        raise DecodeFailure("empty BRep topology")
    RecordsA = ShapeRecords(
        TokensA,
        ShapeCount,
        len(CurvesA),
        CurveTwoDCount,
        len(SurfacesA),
        len(LocationsA),
    )
    RootValue = ReadReference(TokensA, ShapeCount, len(LocationsA))
    if (
        RootValue is None
        or RootValue.Orientation != "+"
        or TokensA.PeekToken() is not None
    ):
        raise DecodeFailure("unsupported BRep root")
    CurvesA, SurfacesA, RecordsA, RootValue = ApplyLocations(
        CurvesA, SurfacesA, RecordsA, RootValue, LocationsA, IdPrefix
    )
    return BuildModel(
        CurvesA,
        SurfacesA,
        RecordsA,
        RootValue,
        IdPrefix,
        DesignBodyId,
        Attributes,
    )


# this definition exists because focused parser behavior needs one stable owner
def DecodeAsciiBrep(
    DataValue: bytes,
    *,
    IdPrefix: str = "occ",
    DesignBodyId: str = "",
    Attributes: Mapping[str, object] | None = None,
) -> BrepModel | None:
    if (
        type(DataValue) is not bytes
        or not DataValue
        or len(DataValue) > KMaxBytes
        or type(IdPrefix) is not str
        or not IdPrefix
        or IdPrefix != IdPrefix.strip()
        or len(IdPrefix) > 256
        or type(DesignBodyId) is not str
        or len(DesignBodyId) > 512
    ):
        return None
    try:
        return DecodePayload(DataValue, IdPrefix, DesignBodyId, Attributes or {})
    except (DecodeFailure, KeyError, TypeError, ValueError, OverflowError):
        return None


# this definition exists because version discovery needs one bounded scanner
def VersionPayload(DataValue: bytes) -> bytes:
    Offset = 0
    while Offset < len(DataValue):
        LineEnd = DataValue.find(b"\n", Offset)
        if LineEnd < 0:
            LineEnd = len(DataValue)
        BodyValue = DataValue[Offset:LineEnd]
        if len(BodyValue) > 99:
            break
        while BodyValue.endswith(b"\r"):
            BodyValue = BodyValue[:-1]
        if BodyValue in KVersionLines:
            if BodyValue != KVersionLine:
                raise DecodeFailure("unsupported BRep version line")
            return DataValue[Offset:]
        if LineEnd == len(DataValue):
            break
        Offset = LineEnd + 1
    raise DecodeFailure("invalid BRep version line")


# this definition exists because structural validation needs one parser pipeline
def ValidateStruct(Payload: bytes) -> None:
    TokensA = Tokens(Payload)
    TokensA.ExpectToken(b"CASCADE")
    TokensA.ExpectToken(b"Topology")
    TokensA.ExpectToken(b"V1,")
    TokensA.ExpectToken(b"(c)")
    TokensA.ExpectToken(b"Matra-Datavision")
    LocationsA = ReadLocations(TokensA)
    CurvesTwoD = ReadCurves(TokensA, b"Curve2ds", 2)
    CurvesThreeD = ReadCurves(TokensA, b"Curves", 3)
    PolygonsThreeD = PolygonThree(TokensA)
    PolygonsOnTriangulations = TriPolygons(TokensA)
    SurfacesA = ReadSurfaces(TokensA)
    TriangulationsA = Triangulations(TokensA)
    ShapeStructure(
        TokensA,
        LocationsA,
        CurvesTwoD,
        CurvesThreeD,
        PolygonsThreeD,
        PolygonsOnTriangulations,
        SurfacesA,
        TriangulationsA,
    )


# this definition exists because public callers need safe structural validation
def IsValidBrep(DataValue: bytes) -> bool:
    if type(DataValue) is not bytes or not DataValue or len(DataValue) > KMaxBytes:
        return False
    try:
        ValidateStruct(VersionPayload(DataValue))
        return True
    except (DecodeFailure, KeyError, TypeError, ValueError, OverflowError):
        return False


# this definition exists because legacy callers need their keyword contract preserved
def DecodeLegacy(DataValue: bytes, **LegacyValues: object) -> BrepModel | None:
    Options = dict(LegacyValues)
    PrefixValue = Options.pop("id_prefix", "occ")
    BodyIdValue = Options.pop("design_body_id", "")
    AttributeValue = Options.pop("attributes", None)
    if Options:
        Unexpected = next(iter(Options))
        raise TypeError(f"decode_ascii_brep got unexpected keyword {Unexpected!r}")
    if not isinstance(PrefixValue, str) or not isinstance(BodyIdValue, str):
        return None
    if AttributeValue is None:
        Attributes: Mapping[str, object] | None = None
    elif isinstance(AttributeValue, Mapping):
        SourceAttributes = Cast(Mapping[object, object], AttributeValue)
        if not all(isinstance(KeyValue, str) for KeyValue in SourceAttributes):
            return None
        Attributes = {
            KeyValue: ItemValue
            for KeyValue, ItemValue in SourceAttributes.items()
            if isinstance(KeyValue, str)
        }
    else:
        return None
    return DecodeAsciiBrep(
        DataValue,
        IdPrefix=PrefixValue,
        DesignBodyId=BodyIdValue,
        Attributes=Attributes,
    )


# legacy parser names remain available to established compatibility consumers
_MAX_BYTES = KMaxBytes
_MAX_GEOMETRY = KMaxGeometry
_MAX_SHAPES = KMaxShapes
_MAX_TOKENS = KMaxTokens
_MIN_INT32 = KMinIntThreeTwo
_MAX_INT32 = KMaxIntThreeTwo
_TOKEN_PATTERN = KTokenPattern
_INTEGER_PATTERN = KIntegerPattern
_FLAGS_PATTERN = KFlagsPattern
_CONTINUITY_PATTERN = KContinuityPattern
_INDEXED_CONTINUITY_PATTERN = KIndexedPattern
_VERSION_LINE = KVersionLine
_VERSION_LINES = KVersionLines
_SHAPE_TYPES = KShapeTypes
_SHAPE_CHILD_TYPES = KShapeChildTypes
_MAX_RECURSION = KMaxRecursion
_MAX_VERTEX_EQUIVALENCE_BUCKET = KMaxVertexBucket
_VERTEX_EQUIVALENCE_DIGITS = KVertexDigits
_IDENTITY_LOCATION = KIdentityLocation
_DecodeFailure = DecodeFailure
_Tokens = Tokens
_Reference = Reference
_VertexData = VertexData
_EdgeData = EdgeData
_FaceData = FaceData
_ShapeRecord = ShapeRecord

# legacy parser names remain available to established compatibility consumers
_vector = VectorValue
_dot = DotValue
_length = LengthValue
_cross = CrossValue
_unit = IsUnit
_IsFrame = IsFrame
_count = ReadCount
_zero_table = ZeroTable
_reference = ReadReference
_boolean = IsBoolean
_numbers = ReadNumbers
_bounded_product = BoundedProduct
_positive_index = PositiveIndex
_location_index = LocationIndex
_continuity = Continuity
_curve_geometry = CurveGeometry
_surface_geometry = SurfaceGeometry
_curves = ReadCurves
_polygon3d = PolygonThree
_polygons_on_triangulations = TriPolygons
_surfaces = ReadSurfaces
_triangulations = Triangulations
_vertex_structure = VertexStructure
_indexed_continuity = IndexContinuity

# legacy parser names remain available to established compatibility consumers
_location_multiply = LocationProduct
_location_power = LocationPower
_normalized_vector = NormalizeVector
_orthogonalized_vectors = OrthoVectors
_location_transform = ParseTransform
_location_product = ProductLocation
_location_inverse = InverseLocation
_location_matrix_power = MatrixPower
_model_locations = ModelLocations
_location_scale = LocationScale
_location_point = LocationPoint
_location_direction = ApplyDirection
_located_model_inputs = LocatedInputs
_locations = ReadLocations

# legacy parser names remain available to established compatibility consumers
_edge_structure = EdgeStructure
_face_structure = FaceStructure
_structural_reference = StructureRef
_shape_structure = ShapeStructure
_vertex_geometry = VertexGeometry
_edge_geometry = EdgeGeometry
_face_geometry = FaceGeometry
_shape_records = ShapeRecords
_ApplyLocations = ApplyLocations
_CanonicalVertexRecords = CanonicalVerts
_OrderWireUses = OrderWireUses

# legacy parser names remain available to established compatibility consumers
_opposite = Opposite
_compose = Compose
_model = BuildModel
decode_ascii_brep = DecodeLegacy
is_structurally_valid_ascii_brep = IsValidBrep
