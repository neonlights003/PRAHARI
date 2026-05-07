import { createContext, useContext, useState, useEffect, type ReactNode } from 'react'

type Role = 'admin' | 'user' | null

interface UserInfo {
    id: number
    name: string
    email: string
}

interface RoleContextType {
    role: Role
    setRole: (role: Role) => void
    isAdmin: boolean
    isAuthenticated: boolean
    isLoading: boolean
    adminToken: string | null
    login: (token: string) => void
    logout: () => void
    userInfo: UserInfo | null
    loginUser: (user: UserInfo) => void
    logoutUser: () => void
}

const RoleContext = createContext<RoleContextType | null>(null)

function parseJwtExp(token: string): number | null {
    try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        return typeof payload.exp === 'number' ? payload.exp : null
    } catch {
        return null
    }
}

function isTokenValid(token: string): boolean {
    const exp = parseJwtExp(token)
    if (exp === null) return false
    return Date.now() / 1000 < exp
}

export function RoleProvider({ children }: { children: ReactNode }) {
    const [role, setRole] = useState<Role>(null)
    const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false)
    const [adminToken, setAdminToken] = useState<string | null>(null)
    const [userInfo, setUserInfo] = useState<UserInfo | null>(null)
    const [isLoading, setIsLoading] = useState<boolean>(true)

    useEffect(() => {
        const savedToken = localStorage.getItem('adminToken')
        const savedRole = localStorage.getItem('userRole') as Role
        const savedUserInfo = localStorage.getItem('userInfo')

        if (savedToken && savedRole === 'admin' && isTokenValid(savedToken)) {
            setAdminToken(savedToken)
            setIsAuthenticated(true)
            setRole('admin')
        } else if (savedUserInfo && savedRole === 'user') {
            try {
                const user = JSON.parse(savedUserInfo)
                setUserInfo(user)
                setRole('user')
            } catch (e) {
                console.error('Failed to parse user info:', e)
            }
        }

        setIsLoading(false)
    }, [])

    const login = (token: string) => {
        setAdminToken(token)
        setIsAuthenticated(true)
        setRole('admin')
        localStorage.setItem('adminToken', token)
        localStorage.setItem('userRole', 'admin')
        // Keep legacy key for any code still checking it
        localStorage.setItem('adminAuthenticated', 'true')
    }

    const logout = () => {
        setAdminToken(null)
        setIsAuthenticated(false)
        setRole(null)
        localStorage.removeItem('adminToken')
        localStorage.removeItem('adminAuthenticated')
        localStorage.removeItem('userRole')
    }

    const loginUser = (user: UserInfo) => {
        setUserInfo(user)
        setRole('user')
        localStorage.setItem('userInfo', JSON.stringify(user))
        localStorage.setItem('userRole', 'user')
    }

    const logoutUser = () => {
        setUserInfo(null)
        setRole(null)
        localStorage.removeItem('userInfo')
        localStorage.removeItem('userRole')
    }

    return (
        <RoleContext.Provider value={{
            role,
            setRole,
            isAdmin: role === 'admin',
            isAuthenticated,
            isLoading,
            adminToken,
            login,
            logout,
            userInfo,
            loginUser,
            logoutUser
        }}>
            {children}
        </RoleContext.Provider>
    )
}

export function useRole() {
    const context = useContext(RoleContext)
    if (!context) {
        throw new Error('useRole must be used within a RoleProvider')
    }
    return context
}
