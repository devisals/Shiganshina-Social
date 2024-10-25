import React, { useState, useEffect } from 'react';
import axios from 'axios';
import Sidebar from "./Sidebar.tsx";
import { useAuth } from './context/auth.tsx';
import { useNavigate } from 'react-router-dom';
import Cookies from 'js-cookie';
import { getIdFromUrlRegex } from './types/Host.tsx';
import './EditProfile.css'

const EditProfile = () => {
  const auth = useAuth();
  const history = useNavigate();

  // State for form fields
  const [profileImage, setProfileImage] = useState('');
  const [github, setGithub] = useState('');
  const [displayName, setDisplayName] = useState('');
//   const [password, setPassword] = useState('');

  // Load current user info
  useEffect(() => {
    if (!auth.user || !auth.user.author) {
      const cookiesAuth = Cookies.get('auth');
      if (cookiesAuth) {
        const authUser = JSON.parse(cookiesAuth);
        auth.setUser(authUser);
      } else {
        history('/login');
        return;
      }
    }

    // Pre-fill form with current user info
    setProfileImage(auth.user.author.profileImage || '');
    setGithub(auth.user.author.github || '');
    setDisplayName(auth.user.author.displayName || '');
  }, [auth.user, history]);

  const handleSubmit = async (e:any) => {
    e.preventDefault();

    // Construct the updated author object
    const changedAuthor = {
      ...auth.user.author,
      displayName,
      github,
      profileImage,
      // Include password change logic as required
    };

    try {
      const refinedAuthorID = getIdFromUrlRegex(auth.user.author.id);
    //   const base64Credentials = btoa(`${displayName}:${password}`);

      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Basic ${auth.user.token}`
      };

      const response = await axios.put(`/api/authors/${refinedAuthorID}`, changedAuthor, { headers });

      // Update auth and cookies with new author data
      // get the new token from the response
      const oldTokenDecoded = atob(auth.user.token);
      const password = oldTokenDecoded.split(':')[1];

      const newToken = btoa(`${displayName}:${password}`);  

      auth.setUser({author: response.data, token:newToken});

      Cookies.set('auth', JSON.stringify({ ...auth.user, author: response.data }));

      alert('Profile updated successfully!');
      history('/profile?id=' + refinedAuthorID);
    } catch (error) {
      console.error('Failed to update profile', error);
      alert('Failed to update profile');
    }
  };

  return (
    <>
      <div className="edit-profile">
        <div className='edit-profile-form'>
        <div className="edit-profile-header">
          <h2>Edit Profile</h2>
        </div>
        <form className="edit-profile-content" onSubmit={handleSubmit}>
          <label>
            Profile Image URL:
            <input type="text" value={profileImage} onChange={(e) => setProfileImage(e.target.value)} />
          </label>
          <label>
            GitHub URL:
            <input type="text" value={github} onChange={(e) => setGithub(e.target.value)} />
          </label>
          <label>
            Display Name:
            <input type="text" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          </label>
          {/* <label>
            Password (leave blank to keep the same):
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label> */}
          <button type="submit">Update Profile</button>
          <button onClick={() => history('/profile?id=' + getIdFromUrlRegex(auth.user.author.id))}>Cancel</button>
        </form>
        </div>
      </div>
    </>
  );
};

export default EditProfile;
