import { DataGrid, GridColDef } from '@mui/x-data-grid';
import * as React from 'react';
import { useStore } from '../store';
import { IconButton } from '@mui/material';
import { Link } from 'react-router-dom';
import DateLabel from './date-label';
import CurrencyLabel from './currency-label';

export default function BudgetTable({ removeBudgetItem }) {
    const columns: GridColDef[] = [
        { field: 'name', headerName: 'Name', width: 200 },
        { field: 'amount', headerName: 'Amount', width: 130, renderCell: (params) => <CurrencyLabel amount={params.value} />},
        { field: 'type', headerName: 'Type', width: 130 },
        { field: 'updated_at', headerName: 'Updated', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'start_date', headerName: 'Start', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        { field: 'end_date', headerName: 'End', width: 130, renderCell: (params) => <DateLabel date={params.value} />},
        // { field: 'group', headerName: 'Group', width: 130, valueFormatter: (params: any) => params?.value?.name},
        { field: 'periods', headerName: 'Periods', width: 380, renderCell: (params) => {
            if (!params.value || !Array.isArray(params.value)) {
                return <span>-</span>;
            }
            return (params.value as any).map((p, pi) => (
                <span key={`${pi}-${p.type}`}>
                    {p.type}-{p.value}
                    {p.businessDay !== 'none'
                        ? ` (${p.businessDay})`
                        : ''}
                    {pi < params.value.length - 1 ? ', ' : ''}
                </span>
            ));
        }},
        // { field: 'monthlyAmount', headerName: 'Monthly', width: 130, valueFormatter: (params: any) => {
        //     return params?.value ? params.value.toLocaleString('USD', {
        //         style: 'currency',
        //         currency: 'USD',
        //     }) : '';
        // }},
        // { field: 'yearlyAmount', headerName: 'Yearly', width: 130, valueFormatter: (params: any) => {
        //     return params?.value ? params.value.toLocaleString('USD', {
        //         style: 'currency',
        //         currency: 'USD',
        //     }) : '';
        // }},
        // { field: 'percentage', headerName: 'Percent', width: 130, valueFormatter: (params: any) => {
        //     return (params.value * 100.0).toFixed(2) + '%';
        // }},
        { field: 'id', headerName: 'Actions', width: 100, renderCell: (params) => (
            <span>
                <IconButton
                    aria-label="delete"
                    className="delete-budget-item-button"
                    onClick={() => {
                        removeBudgetItem(params.value);
                    }}
                >
                    <i className="material-icons">
                        delete
                    </i>
                </IconButton>
                <Link to={`/budget/${params.value}`}>
                    <IconButton
                        aria-label="edit"
                        className="edit-budget-item-button"
                    >
                        <i className="material-icons">
                            edit
                        </i>
                    </IconButton>
                </Link>
            </span>
        )},
    ];
    
    const budget = useStore((state) => (state as any).budget);
    return (
        <DataGrid
            rows={budget}
            columns={columns}
        ></DataGrid>
    );
}
