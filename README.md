# dataclass-serializer

Dataclass serializer, serialize dataclass to json representation.

- Supports nested dataclasses serialize / deserialize
- Type Hint friendly

## Install

```
pip install dataclass-serializer
```

## Usage

```python
import numpy as np
from typing import Optional
from dataclasses import dataclass, field
from dataclass_serializer import Serializable, deserialize


@dataclass
class ExampleClass(Serializable):
    value: str

    # Gives custom serialization for a field
    field_with_serializer: np.ndarray = field(metadata={
        "encode": lambda x: x.tolist(),
        "decode": lambda x: np.array(x),
    })

    # Only fields annotated with `Optional` can be None, and 
    # raise Exception if None given.
    optional_field: Optional[int] = None
    
    # Gives validation logic for each field
    field_with_validation: int = field(default=0, metadata={
        "contract": lambda x: x >= 0,
    })
    
    # Given data class and Serializable will also be
    # serialized / deserialized correctly.
    serializable_field: Optional[Serializable] = None


object = ExampleClass(field="value")

# Generate json serializable dict object
object.serialize()

# Generate object again from json data representation. 
object = deserialize(object.serialize())
```