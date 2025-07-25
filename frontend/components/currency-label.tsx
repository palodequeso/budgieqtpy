import * as React from 'react';


export default function CurrencyLabel({ amount }) {
    const [currency, _] = React.useState('USD');

    return (
        <span>
            {amount ? amount.toLocaleString(currency, {
                style: 'currency',
                currency,
            }) : ''}
        </span>
    );
}