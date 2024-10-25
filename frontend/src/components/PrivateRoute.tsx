import { Outlet, Navigate } from 'react-router-dom';
import { useAuth } from './context/auth'; 

const PrivateRoutes = () => {
    let auth = useAuth();
    // console.log(auth.user.author)
    if (auth.user.author === undefined) {
        return <Navigate to='/login'/>
    }

    return (

        <Outlet />

    )
}

export default PrivateRoutes