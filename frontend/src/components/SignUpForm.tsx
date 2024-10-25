import React, { useState } from 'react';
import './SignUpForm.css'; // Ensure you have a corresponding CSS file for styling
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

const SignUpForm: React.FC = () => {
    const history = useNavigate();
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [github, setGithub] = useState('');
    const [error, setLocalError] = useState('');

    const submit = async (e: React.FormEvent<HTMLFormElement>) => {
        e.preventDefault(); // Prevent the default form submission behavior

        // Example payload. Add "profileImage" if needed
        const payload = {
            displayName: username.trimEnd(), // Ensure `username` is defined in your component state
            password, // Ensure `password` is defined in your component state
            github, // Ensure `github` is defined in your component state
            // profileImage: 'url-to-image', // Uncomment and modify if you're collecting this information
        };

        try {
            // Replace `/api/auth` with your actual endpoint
            const response = await axios.post(`/api/auth`, payload, {
                headers: {
                    'Content-Type': 'application/json',
                },
            });
            // console.log(response.data);
            // Redirect to the login page after successful signup
            history('/login'); // Using `push` method for redirection
        } catch (error: any) {
            console.error(error.response ? error.response.data : error);
            // Providing more detailed error feedback if available
            const errorMessage = error.response && error.response.data && error.response.data.error
                ? error.response.data.error
                : 'An error occurred during signup. Please try again.';
            setLocalError(errorMessage); // Set a more user-friendly error message
        }
    };

    return (
        <div className='signUpFormRoot'>
            <div className="signUpHeader">
                {/* Header content if needed */}
            </div>
            <div className="signUpBody">
                <div className="signUpFormWrapper">
                    <form className="signUpForm" onSubmit={submit}>
                        <h1 className="signUpTitle">Sign Up</h1>
                        <div className="inputWrapper">
                            <input
                                type="text"
                                id="username"
                                placeholder='Username'
                                name="username"
                                value={username}
                                onChange={(event) => setUsername(event.target.value)}
                                required
                            />
                        </div>

                        <div className="inputWrapper">
                            <input
                                type="password"
                                id="password"
                                placeholder='Password'
                                name="password"
                                value={password}
                                onChange={(event) => setPassword(event.target.value)}
                                required
                            />
                        </div>

                        <div className="inputWrapper">
                            <input
                                type="url"
                                id="github"
                                name="github"
                                placeholder='Github Link'
                                value={github}
                                onChange={(event) => setGithub(event.target.value)}
                            />
                        </div>

                        <div className='ButtonContainer'>

                            <button className="signUpButton" type="submit">Sign Up</button>
                            <button className="loginRedirect" onClick={() => history('/login')}>Already a User? Log In</button>
                            <p className="signUpError">{error}</p>
                        </div>
                    </form>
                </div>
            </div>
            <div className="signUpFooter">
                {/* Footer content if needed */}
            </div>
        </div>
    );
};

export default SignUpForm;
