import pytest
from .regression_validation import validate_layer_spec_fields

def test_valid_spec(): validate_layer_spec_fields(1,'A','T01_Project_DNA','x.py','test_*.py')

def test_invalid_number():
    with pytest.raises(ValueError): validate_layer_spec_fields(15,'A','T15','x.py','test_*.py')

def test_invalid_directory():
    with pytest.raises(ValueError): validate_layer_spec_fields(1,'A','../T01','x.py','test_*.py')
