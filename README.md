# myprotein_product_query
## Overview
myprotein has sales literally every other day. They always show prices for the product as "starting at" but do not let you easily see the prices of the flavours. Run this script to query the price information for all their products.

## Run
```Shell
make
```

## Output
The output is a tuple of product name and price, delimited by a tab.
```
"Whey Protein Flavour 2.2 lb"	"$xx.xx"
"Whey Protein Flavour 5.5 lb"	"$xx.xx"
```

Sorting can be done with `sort`.
```
make | sort -k 2 -n -t $'\t'
```
