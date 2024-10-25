import React, { useState, useEffect } from 'react';
import './LoginForm.css'
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { useAuth } from './context/auth';
import { getIdFromUrlRegex } from './types/Host';
import { useCookies } from 'react-cookie';
// import {HOST} from './HOST.tsx';
// import Cookies from 'js-cookie';
// import Navbar from './NavbarDeco.tsx';
// import Footer from './Footer.tsx';

type LoginProps = {
    onLogin: (user: any) => void
}


const LoginForm: React.FC<LoginProps> = ({onLogin}) => {
    const history=useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const userContext = useAuth();
    const [cookies, setCookie] = useCookies(['auth']);
     // If the user changes input, clear the error
     useEffect(() => {
        setError('');
    }, [username, password]);
    async function submit(e: React.FormEvent<HTMLFormElement>) {
        e.preventDefault(); // Prevent the default form submission behavior
    
        const base64Credentials = btoa(`${username.trimEnd()}:${password}`);
        const config = {
            headers: {
                'Authorization': `Basic ${base64Credentials}`,
            }


        };
    
        try {
            const response = await axios.get(`/api/auth`, config);

            // console.log(response); // Logging the response data (user object in this case)
            const data = response.data;
            data.id = data.id.toString();
            // console.log(base64Credentials);
            // make a request to get all the users that the current user is following
            // const refinedID = getIdFromUrlRegex(data.id);
            // const followingResponse = await axios.get(`/api/authors/${refinedID}/following`, config);
            userContext.setUser({author: data, token:base64Credentials}); // Set the user in the context

            // set the auth as cookies in the browser after encoding it to base64
            // encode the AuthUser to base64
            // set the auth as cookies in the browser
            onLogin({author: data, token: base64Credentials});
            history('/'); // Redirect to the home page
        } catch (error) {
            console.error(error);
            const eCast = error as any; // Casting the error to 'any'
            if (eCast.response && eCast.response.status === 401) {
                // Handle unauthorized error
                // console.log(username, password);
                // console.log(base64Credentials);
                setError('Invalid username or password');
            }
        }
    }

    function redirectToSignup() {
        history('/signup');
    }


    return (
        <div className='loginFormRoot'>
            <div className = "header">
   
            </div>
            <div className="body">
                <div className="loginFormWrapper">
                    <form className="loginForm" action="POST" onSubmit={submit}>
                        <h1 className="loginTitle">Log In</h1>
                        <div className="inputWrapper">
                            <input
                                type="text"
                                id="username"
                                name="username"
                                placeholder='Username'
                                value={username}
                                onChange={(event) => setUsername(event.target.value)}
                                required
                            />
                        </div>

                        <div className="inputWrapper">
                            <input
                                type="password"
                                id="password"
                                name="password"
                                placeholder='Password'
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                            />
                        </div>
                        <button className="loginButton" type="submit">Log in</button>
                        <button className="signupredirect" onClick={redirectToSignup}>Not a User? Sign Up</button>
                        <p>{error}</p>
                    </form>
                </div>
            </div>

            <div className = "footer">
         
            </div>
        
        
        </div>

    );
};

export default LoginForm;
