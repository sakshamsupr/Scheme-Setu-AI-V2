import { createContext,useContext,useEffect,useMemo,useState } from 'react';
import { api } from '../services/api';

const Ctx=createContext(null);
export function NotificationProvider({children}){
 const [items,setItems]=useState([]);
 const load=async()=>{try{const r=await api.notifications();setItems(r.items||[])}catch{setItems([])}};
 useEffect(()=>{load()},[]);
 const addReminder=async(rem)=>{try{const created=await api.addReminder(rem);setItems(x=>[created,...x])}catch{const local={...rem,id:`local-${Date.now()}`,type:'reminder',read:false};setItems(x=>[local,...x])}};
 const markRead=(id)=>setItems(x=>x.map(n=>n.id===id?{...n,read:true}:n));
 const markAll=()=>setItems(x=>x.map(n=>({...n,read:true})));
 const unread=items.filter(n=>!n.read).length;
 const value=useMemo(()=>({items,unread,addReminder,markRead,markAll,refresh:load}),[items,unread]);
 return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
export const useNotifications=()=>useContext(Ctx);
