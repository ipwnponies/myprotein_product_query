import json
from unittest import mock
from unittest import TestCase

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


@responses.activate
def test_get_all_products() -> None:
    response = {
        'variations': [
            {
                'id': 100,
                'variation': 'Flavour',
                'options': [
                    {
                        'id': 111,
                        'name': 'flavour_name',
                        'value': 'flavour_value',
                    },
                ],
            },
            {
                'id': 200,
                'variation': 'Amount',
                'options': [
                    {
                        'id': 211,
                        'name': 'size_name1',
                        'value': 'size_value1',
                    },
                    {
                        'id': 222,
                        'name': 'size_name2',
                        'value': 'size_value2',
                    },
                ],
            },
        ],
    }

    product_category_id = '12345'
    responses.add(
        responses.GET,
        f'https://us.myprotein.com/variations.json?productId={product_category_id}',
        body=json.dumps(response),
    )

    flavours, sizes = myprotein.get_all_products(product_category_id)

    assert len(flavours) == 1
    assert flavours[0] == myprotein.Option(111, 'flavour_name', 'flavour_value')

    TestCase().assertCountEqual(
        sizes,
        [
            myprotein.Option(222, 'size_name2', 'size_value2'),
            myprotein.Option(211, 'size_name1', 'size_value1'),
        ],
    )
