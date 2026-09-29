import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import Schemes from './pages/Schemes';
import SchemeDetails from './pages/SchemeDetails';
import Compare from './pages/Compare';
import Calculator from './pages/Calculator';
import Partners from './pages/Partners';
import Documents from './pages/Documents';
import Roadmap from './pages/Roadmap';
import Profile from './pages/Profile';

export default function App(){return <Routes><Route element={<MainLayout/>}>
 <Route path="/" element={<Home/>}/><Route path="/dashboard" element={<Dashboard/>}/><Route path="/schemes" element={<Schemes/>}/><Route path="/schemes/:id" element={<SchemeDetails/>}/><Route path="/compare" element={<Compare/>}/><Route path="/calculator" element={<Calculator/>}/><Route path="/partners" element={<Partners/>}/><Route path="/documents" element={<Documents/>}/><Route path="/roadmap" element={<Roadmap/>}/><Route path="/roadmap/:id" element={<Roadmap/>}/><Route path="/profile" element={<Profile/>}/><Route path="*" element={<Navigate to="/" replace/>}/>
 </Route></Routes>}
