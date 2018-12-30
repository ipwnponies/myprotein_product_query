#! env python
import argparse
import json
import operator
from dataclasses import asdict
from dataclasses import dataclass
# noreorder Disable wrong-import-order until isort is fixed to recognize dataclasses as standard
# noreorder pylint: disable=wrong-import-order
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import addict
import bs4
import requests
from tabulate import tabulate

# noreorder pylint: enable=wrong-import-order

JsonDict = Dict[str, Any]
AddictDict = Any  # pylint: disable=invalid-name

URL = 'http://us.myprotein.com/variations.json?productId={}'
PRODUCT_ID = {
    'whey': '10852500',
    'whey_pouch': '11464969',
    'creatine': '10852411',
}

VOUCHER_URL = 'https://us.myprotein.com/voucher-codes.list'


@dataclass
class ProductInformation:
    flavour: str
    size: str
    price: float


def parse_cli() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--vouchers',
        help='Show current vouchers',
        action='store_true',
    )

    whey_group = parser.add_argument_group('whey')
    whey_group.add_argument(
        '--whey',
        help='Show whey products',
        action='store_true',
    )
    whey_group.add_argument(
        '--whey-size',
        help="Size of products to filter by, e.g. '2.2 lb' '1.1 lb'",
        nargs='+',
    )

    creatine_group = parser.add_argument_group('creatine')
    creatine_group.add_argument(
        '--creatine',
        help='Show creatine products',
        action='store_true',
    )

    return parser.parse_args()


def main() -> None:
    args = parse_cli()

    products = []
    if args.whey:
        products.append(PRODUCT_ID['whey'])
        products.append(PRODUCT_ID['whey_pouch'])

    if args.creatine:
        products.append(PRODUCT_ID['creatine'])

    price_data = get_price_data()
    product_information: List[ProductInformation] = []

    for product in products:
        flavours, sizes = get_all_products(product)

        for flavour in flavours:
            for size in sizes:
                product_id = resolve_options_to_product_id(flavour.id, size.id)
                product_information.append(ProductInformation(flavour.name, size.name, price_data[product_id]))

    print_product_information(product_information)

    if args.vouchers:
        get_all_vouchers()


def print_product_information(product_information: List[ProductInformation]) -> None:
    table = [asdict(i) for i in sorted(product_information, key=operator.attrgetter('size', 'price'))]
    print(tabulate(table, headers='keys'))


def get_all_vouchers() -> None:
    print('Vouchers:')
    print('=' * 80)
    page = requests.get(VOUCHER_URL)
    soup = bs4.BeautifulSoup(page.content, 'html.parser')
    voucher_infos = soup.select('.voucher-info-wrapper')
    for voucher in voucher_infos:
        print(voucher.find('h2').find(text=True))
        voucher_message = voucher.select('.voucher-message')[0]
        message = voucher_message.find_all(text=True)
        message = '\n'.join(message).strip()
        print(message)
        print('-' * 80)


def get_price_data() -> Dict[str, float]:
    """Get price information for skus.

    :return: Mapping from product id to price
    """

    product_id = 10852500
    url = f'https://us.myprotein.com/{product_id}.html'

    response = requests.get(url)
    dom = bs4.BeautifulSoup(response.text, 'html.parser')

    for script in dom.find_all('script', type='application/ld+json'):
        script_json = addict.Dict(json.loads(script.string))

        if 'offers' in script_json:
            price_data = {i.sku: float(i.price) for i in script_json.offers}
            break
    else:
        raise ValueError('Could not find product data from {url}')

    return price_data


def get_all_products(product_id) -> Tuple[List[AddictDict], List[AddictDict]]:
    url = f'http://us.myprotein.com/variations.json?productId={product_id}'
    response = addict.Dict(requests.get(url).json())
    flavours = [
        flavour
        for variation in response.variations
        for flavour in variation.options
        if variation.variation == 'Flavour'
    ]

    sizes = [
        size
        for variation in response.variations
        for size in variation.options
        if variation.variation == 'Amount'
    ]

    return flavours, sizes


def resolve_options_to_product_id(flavour: int, size: int) -> str:
    product_id = 10852500
    response = requests.post(
        f'https://us.myprotein.com/{product_id}.variations',
        json={
            # No idea what this means but it needs to be set to 2.
            # Otherwise API ignores other parameters and returns default product (unflavoured)
            'selected': 2,
            'variation1': '5',  # 5 == Flavour
            'option1': flavour,
            'variation2': '7',  # 7 == Size
            'option2': size,
        },
    )
    response.raise_for_status()

    dom = bs4.BeautifulSoup(response.text, 'html.parser')

    # data-child-id is the attribute that contains the canonical product id
    product_id_node = dom.find(attrs={'data-child-id': True})

    if not product_id_node:
        err_msg = f'Could not get data to resolve options to product id. Url: {response.url}'
        raise ValueError(err_msg)

    return product_id_node['data-child-id']


if __name__ == '__main__':
    main()
