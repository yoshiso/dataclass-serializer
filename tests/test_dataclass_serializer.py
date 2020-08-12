from typing import Optional, List, Dict, Any, Callable, Union
import pytest
import pytz
from collections import OrderedDict
from datetime import date, datetime
from decimal import Decimal
import numpy as np
import dataclasses

from dataclass_serializer import (
    Serializable,
    deserialize,
    partial,
    NoDefaultVar,
    NoDefault,
)


@dataclasses.dataclass
class Item(Serializable):
    value: Any


@dataclasses.dataclass
class ItemWithDefault(Serializable):
    value: Optional[int] = dataclasses.field(default=1)


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


@dataclasses.dataclass
class ItemWithType(Serializable):
    value: type = dataclasses.field()


@dataclasses.dataclass
class ItemWithCallable(Serializable):
    value: Callable = dataclasses.field()


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

    # Case when entity is already serialized before, then later on you added new field to the
    # entity with new default value. In this case, we want to deserialize entity with filling
    # new field with None.

    missing = {"__ser__": "test_dataclass_serializer:ItemWithDefault"}
    assert deserialize(missing) == ItemWithDefault(value=None)

    # Test case with not optional value
    with pytest.raises(ValueError) as e:
        missing = {"__ser__": "test_dataclass_serializer:Item"}
        deserialize(missing)

    assert "unknown" in str(e.value)


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


def test_with_type():

    item = ItemWithType(value=Decimal)

    expect = {
        "value": {"__ser__": "type", "value": "decimal:Decimal"},
        "__ser__": "test_dataclass_serializer:ItemWithType",
    }
    assert item.serialize() == expect

    item.validate()


def test_with_callable():

    item = ItemWithType(value=np.testing.assert_array_almost_equal)

    expect = {
        "value": {
            "__ser__": "function",
            "value": "numpy.testing._private.utils:assert_array_almost_equal",
        },
        "__ser__": "test_dataclass_serializer:ItemWithType",
    }
    assert item.serialize() == expect

    item.validate()


def test_with_module():

    item = Item(value=pytest)

    expect = {
        "value": {"__ser__": "module", "value": "pytest"},
        "__ser__": "test_dataclass_serializer:Item",
    }
    assert item.serialize() == expect

    item.validate()

    assert deserialize(item.serialize()).value == pytest


@dataclasses.dataclass
class ItemWithFields(Serializable):
    value1: Any
    value2: Any


def test_partial():
    # Custom serializagtion logic should be priotized than the default.

    item = partial(ItemWithFields)

    expect = {
        "func": {
            "__ser__": "type",
            "value": "test_dataclass_serializer:ItemWithFields",
        },
        "kwargs": {},
        "__ser__": "dataclass_serializer.dataclass_serializer:Partial",
    }
    assert item.serialize() == expect

    assert item(value1="1", value2="2") == ItemWithFields(value1="1", value2="2")

    item.validate()

    item = partial(ItemWithFields, value1="value1")

    # Could not initialized without sufficient parameters
    with pytest.raises(TypeError):
        item()

    with pytest.raises(TypeError):
        # Returns result once satisfys condition, also confirmed support of parameter overwrite
        assert item(value1="update", value2="value2") == ItemWithFields(
            value1="update", value2="value2"
        )

    with pytest.raises(TypeError):
        # Returns result once satisfys condition, also confirmed support of parameter overwrite
        assert item(vvalue2="value2") == ItemWithFields(
            value1="update", value2="value2"
        )


@dataclasses.dataclass
class ItemWithNoDefault(Serializable):
    value: NoDefaultVar[int] = NoDefault()


def test_no_default():

    with pytest.raises(TypeError):
        ItemWithNoDefault()

    # Can be initialized with
    ItemWithNoDefault(value=1)
