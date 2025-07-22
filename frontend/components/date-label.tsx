import * as React from 'react';
import * as moment from 'moment';

export default function DateLabel({ date }) {
    const [dateFormat, _] = React.useState('MM/DD/yyyy');
    const [dateString, setDateString] = React.useState('');

    React.useEffect(() => {
        if (date) {
            setDateString(moment(date).format(dateFormat));
        } else {
            setDateString('');
        }
    }, [date]);

    return (
        <span>
            {dateString}
        </span>
    );
}