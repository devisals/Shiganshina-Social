import {createContext, useState,useContext} from "react"
import { Author } from "../types/Author";

// modify later to hold jwt token

export type AuthUser = {
    author: Author;
    token: string;
}


type UserContextType = {
    user: AuthUser;
    setUser: (user: AuthUser) => void;
}

type UserContextProviderType = {
    children: React.ReactNode;
}

export const UserContext = createContext({} as UserContextType);

export const UserContextProvider = ({children} : UserContextProviderType) => {
    const [user, setUser] = useState({} as AuthUser);

    return (
        <UserContext.Provider value={{user, setUser}}>
            {children}
        </UserContext.Provider>
    )
}

export const useAuth = () => {
    return useContext(UserContext);
}



