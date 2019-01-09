import pytest
import responses

import myprotein


@pytest.fixture(autouse=True)
def mock_responses():  # type: ignore
    with responses.RequestsMock():
        yield


@responses.activate
def test_get_price_data() -> None:
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
