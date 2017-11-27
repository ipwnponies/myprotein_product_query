#! env python
import argparse

import bs4
import requests

URL = 'http://us.myprotein.com/variations.json?productId={}'
PRODUCT_ID = {
    'whey': '10852500',
    'creatine': '10852411',
}

VOUCHER_URL = 'https://us.myprotein.com/voucher-codes.list'


def parse_cli():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--whey',
        help='Show whey products',
        action='store_true',
    )
    parser.add_argument(
        '--creatine',
        help='Show creatine products',
        action='store_true',
    )
    parser.add_argument(
        '--vouchers',
        help='Show current vouchers',
        action='store_true',
    )

    return parser.parse_args()


def main():
    args = parse_cli()

    products = []
    if args.whey:
        products.append(PRODUCT_ID['whey'])

    if args.creatine:
        products.append(PRODUCT_ID['creatine'])

    for product in products:
        flavours, pouches, sizes = get_all_products(product)

        for i in flavours:
            for k in sizes:
                get_price(product, i['id'], pouches[0]['id'], k['id'])

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


def get_all_products(product_id):
    combinations = requests.get(URL.format(product_id)).json()['variations']
    flavours = combinations[0]['options']
    pouches = combinations[1]['options']
    sizes = combinations[2]['options']

    return flavours, pouches, sizes


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
