# myprotein_product_query

[![Build Status](https://travis-ci.com/ipwnponies/myprotein_product_query.svg?branch=master)](https://travis-ci.com/ipwnponies/myprotein_product_query)

## Overview

myprotein has sales literally every other day.
They always show prices for the product as "starting at" but do not let you easily see the prices of the flavours.
Run this script to query the price information for all their products.

## Quickstart

```Shell
make help

make run
OR
virtualenv_run/bin/python myprotein [--whey] [--creatine] [--vouchers]
```

## Output

The output is a tuple of product name and price, delimited by a tab.

    "Whey Protein Flavour 2.2 lb"   "$xx.xx"
    "Whey Protein Flavour 5.5 lb"   "$xx.xx"

Sorting can be done with `sort`.

```sh
make | sort -k 2 -n -t $'\t'
```

## Details of mypotein API

Quick overview.
Flavours have ids.
Sizes have ids.
This tuple resolves to a product id, which uniquely identifies the sku.
So this script will generate all possible skus and their pricing.

To get pricing information, we scrape the product page (`/{product_id}.html`).
This returns, in the html, prices for all the product ids.

`GET` to `/variations.json?productId={product_id}` to get all possible flavour and size combinations.
The cartesian product of flavour and size results in all possible sku combinations.
But we need to resolve to sku first.

Query `/{product_id}.variations` with flavour and size options in json body:

```json
{
    # No idea what this means but it needs to be set to 2.
    # Otherwise API ignores other parameters and returns default product (unflavoured)
    'selected': 2,
    'variation1': '5',  # 5 == Flavour
    'option1': flavour_id,
    'variation2': size,  # 7 == Size
    'option2': size_id,
}
```

This will give an html output but somewhere in there is the product id as a data-* attribute.

I don't claim to understand what the tech stack is but I wonder why JSON responses were insufficient.
