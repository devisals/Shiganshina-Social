import React, { useEffect } from 'react';
import './searchBar.css'
import axios from 'axios';
import { ListClassKey, ListItemSecondaryAction } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { getIdFromUrlRegex } from './types/Host';
import { ArrowBack } from '@mui/icons-material';

const UserFind: React.FC = () => {
    const [users, setUsers] = React.useState([]);
    const history = useNavigate();
    useEffect(() => {
        async function getAllAuthors() {
            try {
                const response = await axios.get(`/api/authors?size=1000&page=1&all`);
                const authors = response.data.items;
                setUsers(authors);
            } catch (error) {
                console.error('Failed to fetch authors:', error);
            }
        }

        getAllAuthors();

    }, [history]);

    const [text, setText] = React.useState('');
    const getFilteredItems = (text: string, users: any) => {
        if (!text) {
            return users;
        }
        return users.filter((user: any) => user.displayName.includes(text))
    }

    function viewProfile(author: any) {
        const authorId = getIdFromUrlRegex(author.id);
        history('/profile?id=' + authorId);
    }
    const filteredItems = getFilteredItems(text, users)
    return (
        <div>
            <div className='title'>
                <button className="backbtn" onClick={() => history('/')}><ArrowBack /></button>
                <h1>User find </h1>
            </div>
            <div className='search_input_wrapper'>
                <input type="text" placeholder='Search'
                    value={text}
                    onChange={e => setText(e.target.value)} />
                <button>Search</button>
                <ul>
                    <div className='search-each-item'>
                        {filteredItems.map((value: any) =>
                            <div key={value.name} className='outerSearchText' onClick={() => viewProfile(value)}>
                                <div className='searchImage'>
                                    <img src={value.profileImage}></img></div>
                                <div className='InnerSearchText'>
                                    <h1 key={value.name}>{value.displayName} </h1>
                                    <h5>@{value.github}</h5></div></div>)}
                    </div>
                </ul>
            </div>
        </div>
    );
};


export default UserFind;