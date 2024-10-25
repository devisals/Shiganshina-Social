import {UserContextProvider} from './components/context/auth.tsx';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Home from './components/Home.tsx';
import PrivateRoute from './components/PrivateRoute.tsx';
import UserPage from './components/UserPage.tsx';
import LoginForm from './components/LoginForm.tsx';
import SignUpForm from './components/SignUpForm.tsx';
import EditProfile from './components/EditProfile.tsx';
import UserFind from './components/searchBar.tsx';
import { Cookies, CookiesProvider, useCookies } from 'react-cookie';
import Inbox from './components/Inbox.tsx';
function App() {
  const [cookies, setCookie] = useCookies(['auth']);
  function onLogin(user: any) {
    setCookie('auth', user, { path: '/' });
    // console.log('cookies', cookies);
  }
  return (
    <> 

        <UserContextProvider>
        <CookiesProvider>
            <Router>
                <Routes>
        

                    <Route path="/" element={<Home />} />
         
                    <Route path="/profile" element={<UserPage />} />

                    <Route path="/editprofile" element={<EditProfile />} />

                    <Route path="/login" element={<LoginForm onLogin={onLogin}/>} />

                    <Route path="/signup" element={<SignUpForm />} />

                    <Route path="/search" element={<UserFind />} />

                    <Route path="/inbox" element={<Inbox />} />



    
 
                       

                    
                </Routes>
            </Router>
          </CookiesProvider>
        </UserContextProvider>

    </>

  )
}

export default App
