from unittest import mock

import pytest
import responses

import myprotein
from myprotein import ProductInformation


@pytest.fixture(autouse=True)
def mock_responses():  # type: ignore
    with responses.RequestsMock():
        yield


@responses.activate
def test_get_price_data() -> None:
    """Test that get_price_data can parse price data from request."""
    product_category_id = 'test_category'
    body = r'''
<html>

// Not used
<script type="text/html">
{
    "offers": {
        {"sku": "123", "price": "123.00"}
    }
}
</script>

// This is target
<script type="application/ld+json">
{
    "offers": [
        {"sku": "456", "price": "456.00"},
        {"sku": "999", "price": "999.00"}
    ]
}
</script>

// Not used
<script type="application/json">
{
    "offers": {
        {"sku": "789", "price": "789.00"}
    }
}
</script>
</html>
    '''
    responses.add(
        responses.GET,
        f'https://us.myprotein.com/{product_category_id}.html',
        body=body,
        content_type='text/html',
    )

    actual = myprotein.get_price_data(product_category_id)

    assert actual == {
        '456': 456.0,
        '999': 999.0,
    }


def test_get_product_information() -> None:
    """Test that get_product_information returns product category key."""
    product_info = {
        '12345': ProductInformation('test_name', 'test_flavour', 'test_size', 9.9),
    }
    with mock.patch.object(myprotein, 'PRODUCT_INFORMATION', product_info, spec_set=True):
        assert myprotein.get_product_information('test_name') == '12345'


def test_get_product_information_not_found() -> None:
    """Test that get_product_information raises Error if product is not in known list."""
    product_info = {
        '12345': ProductInformation('test_name', 'test_flavour', 'test_size', 9.9),
    }
    with mock.patch.object(myprotein, 'PRODUCT_INFORMATION', product_info, spec_set=True):
        with pytest.raises(Exception):
            myprotein.get_product_information('not a real thing')
