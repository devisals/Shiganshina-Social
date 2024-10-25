import React, { useState, useEffect } from 'react';
import { useAuth } from './context/auth.tsx';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import axios from 'axios';
import InboxContainer from './InboxContainer.tsx';
import './inbox.css'
import { getIdFromUrlRegex } from './types/Host.tsx';
const Inbox:React.FC = () => {
  const history = useNavigate();
  const auth = useAuth();
  const [inboxItemsRaw, setInboxItemsRaw] = useState([]);
  
  const fetchInboxItems = async () => {
    try {
        const refinedUserID = getIdFromUrlRegex(auth.user.author.id)
        const response = await axios.get(`/api/authors/${refinedUserID}/inbox?size=1000&page=1`);
        setInboxItemsRaw(response.data.items);
        // console.log(response.data.items);
    } catch (error) {
        console.error('Failed to fetch inbox items:', error);
        history('/');
    }
  }
  
  useEffect(() => {
     
    const cookiesAuth = Cookies.get('auth');
    // console.log('cookies', cookiesAuth);
    // check if the user is logged in

    if (!auth.user.author) {
      // check the cookies
      if (cookiesAuth){
        const authUser = JSON.parse(cookiesAuth);
        // console.log('cookies', authUser);
        auth.setUser(authUser);
      } else {
        history('/');
      }
    }

    fetchInboxItems();

  }, [history, auth]);

  async function clearInbox() {
    if (!auth.user) return;
    if (!auth.user.author) return;
    if (!inboxItemsRaw) return;
    try {
      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth.user.token}`
      };
      const refinedUserID = getIdFromUrlRegex(auth.user.author.id)
      await axios.delete(`/api/authors/${refinedUserID}/inbox`, {headers});
      setInboxItemsRaw([]);
    } catch (error) {
      setInboxItemsRaw([]);
      console.error('Failed to clear inbox:', error);

    }
  }

  function returnHome() { 
    history('/');
  }

  function refreshInbox() {
    fetchInboxItems();
  }

  return (
    <>

    <div className="inbox-outer">
        <h1>Inbox</h1>

        <InboxContainer inboxItems={inboxItemsRaw} />
          <div className='inbox-button-container'>
          <button className="inbox-button" onClick={clearInbox}>Clear Inbox</button>
          <button className="inbox-button" onClick={returnHome}>Back</button>
          <button className="inbox-button" onClick={refreshInbox}>Refresh Inbox</button>
        </div>
    </div>

    </>
  );
}

export default Inbox;
