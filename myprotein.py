#! env python
import argparse
import json
from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

import addict
import bs4
import requests

JsonDict = Dict[str, Any]

URL = 'http://us.myprotein.com/variations.json?productId={}'
PRODUCT_ID = {
    'whey': '10852500',
    'whey_pouch': '11464969',
    'creatine': '10852411',
}

VOUCHER_URL = 'https://us.myprotein.com/voucher-codes.list'


def parse_cli():
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


def main():
    args = parse_cli()

    products = []
    if args.whey:
        products.append(PRODUCT_ID['whey'])
        products.append(PRODUCT_ID['whey_pouch'])

    if args.creatine:
        products.append(PRODUCT_ID['creatine'])

    for product in products:
        flavours, sizes = get_all_products(product)

        for i in flavours:
            if args.whey_size:
                sizes = [i for i in sizes if i['name'] in args.whey_size]
            for k in sizes:
                get_price(product, i['id'], None, k['id'])

    print()

    if args.vouchers:
        get_all_vouchers()


def get_all_vouchers():
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


def get_all_products(product_id) -> Tuple[List[JsonDict], List[JsonDict]]:
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


def get_price(product_id, flavour_id, package_id, size_id):
    data = {
        'selected': 3,
        'variation1': 5,
        'option1': flavour_id,
        'variation2': 6,
        'option2': package_id,
        'variation3': 7,
        'option3': size_id,
    }
    response = requests.post(URL.format(product_id), data).json()

    try:
        price = response['price'][5:]
        print('{:70}\t{}'.format(
            response['title'],
            price,
        ))
    except KeyError:
        price = None

    return price


if __name__ == '__main__':
    main()
