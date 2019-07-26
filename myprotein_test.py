# Disable redefined function name warning because that's how pytest fixtures work by default
# pylint: disable=redefined-outer-name
import json
from typing import Any
from typing import Iterator
from unittest import mock
from unittest import TestCase

import pytest
import responses

import myprotein
from myprotein import ProductInformation


@pytest.fixture(autouse=True)
def mocked_responses() -> Any:
    with responses.RequestsMock(assert_all_requests_are_fired=False) as _responses:
        yield _responses


@pytest.fixture
def mock_responses_with_default_product_information(mocked_responses: Any) -> Iterator[Any]:
    '''Add default product fallback response.'''

    product_category_id = '10852500'

    default_product_response = '''
    <div
        data-variation-container="productVariations"
        data-child-id="1111"
        data-information-url="sports-nutrition/creatine-monohydrate-unflavoured-0.5lbs/10852413.html"
        data-information-current-quantity-basket="0"
        data-information-maximum-allowed-quantity="5000"
    >
    '''

    mocked_responses.add(
        responses.GET,
        f'https://us.myprotein.com/{product_category_id}.variations',
        body=default_product_response,
        content_type='text/html',
    )
    yield mocked_responses


def test_get_price_data(mocked_responses: Any) -> None:
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
    mocked_responses.add(
        responses.GET, f'https://us.myprotein.com/{product_category_id}.html', body=body, content_type='text/html'
    )

    actual = myprotein.get_price_data(product_category_id)

    assert actual == {'456': 456.0, '999': 999.0}


def test_get_price_data_bad_response(mocked_responses: Any) -> None:
    product_category_id = 'test_category'
    body = r'''
<html>
// No data here
<script type="application/ld+json">
{
}
</script>
</html>
    '''
    mocked_responses.add(
        responses.GET, f'https://us.myprotein.com/{product_category_id}.html', body=body, content_type='text/html'
    )

    with pytest.raises(ValueError):
        myprotein.get_price_data(product_category_id)


def test_get_product_information() -> None:
    """Test that get_product_information returns product category key."""
    product_info = {'12345': ProductInformation('test_name', 'test_flavour', 'test_size', 9.9)}
    with mock.patch.object(myprotein, 'PRODUCT_INFORMATION', product_info, spec_set=True):
        assert myprotein.get_product_information('test_name') == '12345'


def test_get_product_information_not_found() -> None:
    """Test that get_product_information raises Error if product is not in known list."""
    product_info = {'12345': ProductInformation('test_name', 'test_flavour', 'test_size', 9.9)}
    with mock.patch.object(myprotein, 'PRODUCT_INFORMATION', product_info, spec_set=True):
        with pytest.raises(Exception):
            myprotein.get_product_information('not a real thing')


def test_get_all_products(mocked_responses: Any) -> None:
    response = {
        'variations': [
            {
                'id': 100,
                'variation': 'Flavour',
                'options': [{'id': 111, 'name': 'flavour_name', 'value': 'flavour_value'}],
            },
            {
                'id': 200,
                'variation': 'Amount',
                'options': [
                    {'id': 211, 'name': 'size_name1', 'value': 'size_value1'},
                    {'id': 222, 'name': 'size_name2', 'value': 'size_value2'},
                ],
            },
        ]
    }

    product_category_id = '12345'
    mocked_responses.add(
        responses.GET,
        f'https://us.myprotein.com/variations.json?productId={product_category_id}',
        body=json.dumps(response),
    )

    flavours, sizes = myprotein.get_all_products(product_category_id)

    assert len(flavours) == 1
    assert flavours[0] == myprotein.Option(111, 'flavour_name', 'flavour_value')

    TestCase().assertCountEqual(
        sizes, [myprotein.Option(222, 'size_name2', 'size_value2'), myprotein.Option(211, 'size_name1', 'size_value1')]
    )


def test_resolve_options_to_product_id(mock_responses_with_default_product_information: Any) -> None:
    flavour = myprotein.Option(111, 'name', 'value')
    size = myprotein.Option(222, 'name', 'value')
    # impact whey
    product_category_id = '10852500'

    # pylint: disable=line-too-long
    body = '''
<div
    data-variation-container="productVariations"
    data-child-id="10852413"
    data-information-url="sports-nutrition/creatine-monohydrate-unflavoured-0.5lbs/10852413.html"
    data-information-current-quantity-basket="0"
    data-information-maximum-allowed-quantity="5000"
>
    <div class="productVariations_dropdownSegment">
<label class="productVariations_dropdownLabel">Flavor</label>

<select
    class="productVariations_dropdown"
    data-dropdown-type="default"
    data-variation-id="5"
    data-dropdown="productVariation"
    data-variation-id="5"
>
<option value="21686" data-display-text-id="0"
selected>
Unflavored
</option>

</select>
</div>

<div class="productVariations_dropdownSegment">
<label class="productVariations_dropdownLabel">Amount</label>

<select
    class="productVariations_dropdown"
    data-dropdown-type="default"
    data-variation-id="7"
    data-dropdown="productVariation"
    data-variation-id="7"
>
<option value="16221" data-display-text-id="0"
selected>
0.5 lb
</option>
<option value="16220" data-display-text-id="0"
>
1.1 lb
</option>
<option value="16222" data-display-text-id="0"
>
2.2 lb
</option>

</select>
</div>


</div>
</div>
'''
    # pylint: enable=line-too-long
    mock_responses_with_default_product_information.add(
        responses.POST,
        f'https://us.myprotein.com/{product_category_id}.variations',
        body=body,
        content_type='text/html',
    )

    product_id = myprotein.resolve_options_to_product_id(product_category_id, flavour, size)

    assert product_id == '10852413'


def test_resolve_options_to_product_id_default_product(mock_responses_with_default_product_information: Any) -> None:
    '''Test when default product is queried.

    myprotein returns default product when given invalid input. So there's logic to detect that. Then there's logic to
    detect tat it was actually teh default product queried.
    '''

    # impact whey
    product_category_id = '10852500'

    # Queried option matches the default product
    flavour = myprotein.Option(111, 'Unflavored', 'Unflavored')
    size = myprotein.Option(222, '2.2 lb', '2.2 lb')

    product_response = '''
    <div
        data-variation-container="productVariations"
        data-child-id="{}"
        data-information-url="sports-nutrition/creatine-monohydrate-unflavoured-0.5lbs/10852413.html"
        data-information-current-quantity-basket="0"
        data-information-maximum-allowed-quantity="5000"
    >
    '''.format(
        product_category_id
    )

    mock_responses_with_default_product_information.add(
        responses.POST,
        f'https://us.myprotein.com/{product_category_id}.variations',
        body=product_response,
        content_type='text/html',
    )

    product_id = myprotein.resolve_options_to_product_id(product_category_id, flavour, size)
    assert product_id == product_category_id


def test_resolve_options_to_product_id_product_not_found(mock_responses_with_default_product_information: Any) -> None:
    '''Test product not found detection.

    myprotein returns the default product when given invalid input and there was logic to infer this behaviour.
    '''

    # impact whey
    product_category_id = '10852500'

    # Queried options do not match default product
    flavour = myprotein.Option(111, 'name', 'value')
    size = myprotein.Option(222, 'name', 'value')

    default_product_response = '''
    <div
        data-variation-container="productVariations"
        data-child-id="1111"
        data-information-url="sports-nutrition/creatine-monohydrate-unflavoured-0.5lbs/10852413.html"
        data-information-current-quantity-basket="0"
        data-information-maximum-allowed-quantity="5000"
    >
    '''

    mock_responses_with_default_product_information.add(
        responses.POST,
        f'https://us.myprotein.com/{product_category_id}.variations',
        body=default_product_response,
        content_type='text/html',
    )

    with pytest.raises(myprotein.ProductNotExistError):
        myprotein.resolve_options_to_product_id(product_category_id, flavour, size)


def test_resolve_options_to_product_id_bad_response(mock_responses_with_default_product_information: Any) -> None:
    '''Test that invalid http response is handled.

    If data can not be retrieved from response, throw ValueError.
    '''

    # impact whey
    product_category_id = '10852500'
    flavour = myprotein.Option(111, 'name', 'value')
    size = myprotein.Option(222, 'name', 'value')

    mock_responses_with_default_product_information.add(
        responses.POST,
        f'https://us.myprotein.com/{product_category_id}.variations',
        body='''<div></div>''',
        content_type='text/html',
    )

    with pytest.raises(ValueError):
        myprotein.resolve_options_to_product_id(product_category_id, flavour, size)


@pytest.mark.usefixtures('mock_responses_with_default_product_information')
def test_get_default_product_not_found() -> None:
    # Same as in fixture, because that's the default value
    product_category_id = '10852500'

    default_product_id = myprotein.get_default_product_not_found(product_category_id)

    # From fixture hardcoded response
    assert default_product_id == '1111'


def test_get_default_product_not_found_bad_response(mock_responses_with_default_product_information: Any) -> None:
    # Same as in fixture, because that's the default value
    product_category_id = '10852500'

    mock_responses_with_default_product_information.replace(
        responses.GET, f'https://us.myprotein.com/{product_category_id}.variations', body='', content_type='text/html'
    )

    with pytest.raises(ValueError, match='Could not get data to resolve options to product id.'):
        myprotein.get_default_product_not_found(product_category_id)
