import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../views/LandingPage/LandingPage.vue'
import LoginPage from '../views/LoginPage/LoginPage.vue'
import RegisterPage from '../views/RegisterPage/RegisterPage.vue'
import ForgotPasswordPage from '../views/ForgotPasswordPage/ForgotPasswordPage.vue'
import ResetPasswordPage from '../views/ResetPasswordPage/ResetPasswordPage.vue'
import VerifyEmailPage from '../views/VerifyEmailPage/VerifyEmailPage.vue'
import HomePage from '../views/HomePage/HomePage.vue'
import DashboardPage from '../views/DashboardPage/DashboardPage.vue'
import EnergyPage from '../views/EnergyPage/EnergyPage.vue'
import AlertsPage from '../views/AlertsPage/AlertsPage.vue'
import ManagePage from '../views/ManagePage/ManagePage.vue'
import MyHousesPage from '../views/MyHousesPage/MyHousesPage.vue'
import AccountPage from '../views/AccountPage/AccountPage.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: LandingPage
  },
  {
    path: '/login',
    name: 'Login',
    component: LoginPage
  },
  {
    path: '/register',
    name: 'Register',
    component: RegisterPage
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: ForgotPasswordPage
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: ResetPasswordPage
  },
  {
    path: '/verify-email',
    name: 'VerifyEmail',
    component: VerifyEmailPage
  },
  {
    path: '/home',
    name: 'Home',
    component: HomePage
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: DashboardPage
  },
  {
    path: '/energy',
    name: 'Energy',
    component: EnergyPage
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: AlertsPage
  },
  {
    path: '/manage',
    name: 'Manage',
    component: ManagePage
  },
  {
    path: '/myhouses',
    name: 'MyHouses',
    component: MyHousesPage
  },
  {
    path: '/account',
    name: 'Account',
    component: AccountPage
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
