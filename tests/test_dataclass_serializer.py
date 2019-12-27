from typing import Optional, List, Dict, Any
import pytest
import pytz
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal
import numpy as np
import dataclasses

from dataclass_serializer import Serializable, deserialize


@dataclasses.dataclass
class Item(Serializable):
    value: Any


@dataclasses.dataclass
class ItemWithDefault(Serializable):
    value: int = dataclasses.field(default=1)


@dataclasses.dataclass
class ItemWithDefaultFactory(Serializable):
    value: List = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class NestedItem(Serializable):
    value: Item


@dataclasses.dataclass
class NestedList(Serializable):
    value: List


@dataclasses.dataclass
class NestedDictItem(Serializable):
    value: Dict[str, Item]


@dataclasses.dataclass
class ItemWithOptional(Serializable):
    value: Optional[int]


@dataclasses.dataclass
class NDArray(Serializable):
    value: np.ndarray = dataclasses.field(
        metadata={"encode": lambda x: x.tolist(), "decode": lambda x: np.array(x)}
    )

    def __eq__(self, other):
        return [(self.value == other.value).all()]


@dataclasses.dataclass
class ItemWithContract(Serializable):
    value: Optional[Any] = dataclasses.field(metadata={"contract": lambda x: x > 0})


@dataclasses.dataclass
class ItemWithCustomSerialize(Serializable):
    value: Optional[Any] = dataclasses.field(
        metadata={"encode": lambda x: x + "---", "decode": lambda x: x[:-3]}
    )


def test_serializable_class_behavior():
    with pytest.raises(TypeError):
        Item()

    expect = {"value": 1, "__ser__": "test_dataclass_serializer:Item"}

    assert Item(value=1).serialize() == expect

    assert deserialize(expect) == Item(value=1)


def test_serializable_with_default():

    expect = {"value": 1, "__ser__": "test_dataclass_serializer:ItemWithDefault"}

    assert ItemWithDefault().serialize() == expect

    assert deserialize(expect) == ItemWithDefault(value=1)

    # if serialized data missing field, but there is default value then allow to
    # deserialize with default value.
    missing = {"__ser__": "test_dataclass_serializer:ItemWithDefault"}
    assert deserialize(missing) == ItemWithDefault(value=1)


def test_serializable_with_default_factory():

    expect = {
        "value": [],
        "__ser__": "test_dataclass_serializer:ItemWithDefaultFactory",
    }

    assert ItemWithDefaultFactory().serialize() == expect

    assert deserialize(expect) == ItemWithDefaultFactory(value=[])

    # if serialized data missing field, but there is default value then allow to
    # deserialize with default value.
    missing = {"__ser__": "test_dataclass_serializer:ItemWithDefaultFactory"}
    assert deserialize(missing) == ItemWithDefaultFactory()


def test_serializable_with_nested():
    expect = {
        "value": {"value": 5, "__ser__": "test_dataclass_serializer:Item"},
        "__ser__": "test_dataclass_serializer:NestedItem",
    }

    nested = NestedItem(Item(value=5))

    nested.validate()

    assert nested.serialize() == expect

    assert deserialize(expect) == NestedItem(Item(value=5))


def test_serializable_with_nested_list():
    expect = {
        "value": [{"value": 5, "__ser__": "test_dataclass_serializer:Item"}],
        "__ser__": "test_dataclass_serializer:NestedList",
    }

    nested = NestedList(value=[Item(value=5)])
    nested.validate()

    assert nested.serialize() == expect

    assert deserialize(expect) == NestedList(value=[Item(value=5)])


def test_serializable_with_tuple():
    expect = {
        "value": {"__ser__": "tuple", "value": [3, 1]},
        "__ser__": "test_dataclass_serializer:NestedList",
    }

    tuple_item = NestedList(value=(3, 1))
    tuple_item.validate()

    assert tuple_item.serialize() == expect

    assert deserialize(expect) == NestedList(value=(3, 1))

    expect = {
        "value": {
            "__ser__": "tuple",
            "value": [
                {"__ser__": "tuple", "value": [3]},
                {"__ser__": "tuple", "value": [1]},
            ],
        },
        "__ser__": "test_dataclass_serializer:NestedList",
    }

    tuple_item = NestedList(value=((3,), (1,)))

    assert tuple_item.serialize() == expect

    assert deserialize(expect) == NestedList(value=((3,), (1,)))


def test_serializable_with_nested_dict():
    expect = {
        "value": {"key": {"value": 5, "__ser__": "test_dataclass_serializer:Item"}},
        "__ser__": "test_dataclass_serializer:NestedDictItem",
    }

    nested = NestedDictItem(value=dict(key=Item(value=5)))
    nested.validate()
    assert nested.serialize() == expect

    assert deserialize(expect) == NestedDictItem(value=dict(key=Item(value=5)))


def test_serializable_with_optional():

    with pytest.raises(TypeError):
        Item(value=None).validate()

    item = ItemWithOptional(value=None)
    item.validate()

    expect = {"value": None, "__ser__": "test_dataclass_serializer:ItemWithOptional"}

    assert item.serialize() == expect

    assert deserialize(expect) == ItemWithOptional(value=None)


def test_serializable_with_ndarray():

    item = NDArray(value=np.zeros((2, 4)))

    expect = {
        "value": [[0, 0, 0, 0], [0, 0, 0, 0]],
        "__ser__": "test_dataclass_serializer:NDArray",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == NDArray(value=np.zeros((2, 4)))


def test_ordered_dict():
    item = NestedDictItem(value=OrderedDict([(3, "a"), (2, "c")]))

    expect = {
        "value": {"__ser__": "OrderedDict", "value": [[3, "a"], [2, "c"]]},
        "__ser__": "test_dataclass_serializer:NestedDictItem",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == NestedDictItem(
        value=OrderedDict([(3, "a"), (2, "c")])
    )


def test_date():
    item = Item(value=date(2015, 11, 11))

    expect = {
        "value": {"__ser__": "date", "value": "20151111"},
        "__ser__": "test_dataclass_serializer:Item",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == Item(value=date(2015, 11, 11))


def test_datetime():
    now = datetime.now(tz=pytz.utc)
    item = Item(value=now)

    expect = {
        "value": {"__ser__": "datetime", "value": now.isoformat()},
        "__ser__": "test_dataclass_serializer:Item",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == Item(value=now)


def test_decimal():

    item = Item(value=Decimal("0.02521"))

    expect = {
        "value": {"__ser__": "Decimal", "value": "0.02521"},
        "__ser__": "test_dataclass_serializer:Item",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == Item(value=Decimal("0.02521"))


def test_set():

    item = Item(value=set([1, 2, 3]))

    expect = {
        "value": {"__ser__": "set", "value": [1, 2, 3]},
        "__ser__": "test_dataclass_serializer:Item",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == Item(value=set([1, 2, 3]))


def test_with_contract():

    item = ItemWithContract(value=None)

    assert deserialize(item.serialize()) == item

    with pytest.raises(ValueError):
        ItemWithContract(value=-1)

    ItemWithContract(value=3)


def test_to_dict():

    item = Item(value=1)
    assert item.to_dict() == {"value": 1}

    # must be shallow transformation
    item = Item(value=Item(value=1))
    assert item.to_dict() == {"value": Item(value=1)}


def test_with_custom_encoder():
    # Custom serializagtion logic should be priotized than the default.

    item = ItemWithCustomSerialize(value="value")

    expect = {
        "value": "value---",
        "__ser__": "test_dataclass_serializer:ItemWithCustomSerialize",
    }
    item.validate()

    assert item.serialize() == expect

    assert deserialize(expect) == ItemWithCustomSerialize(value="value")

