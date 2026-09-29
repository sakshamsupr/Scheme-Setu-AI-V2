import logo from '../assets/scheme_setu_generated_logo.png';
import symbol from '../assets/scheme_setu_symbol.webp';
export default function BrandLogo({compact=false}){
 return <div className={`brand-lockup ${compact?'compact':''}`}>
   <div className="brand-symbol-wrap"><img src={compact?symbol:logo} alt="Scheme Setu AI logo" className="brand-symbol-art"/></div>
   {!compact&&<div className="brand-wordmark"><strong>Scheme Setu <em>AI</em></strong><span>Bharat's finance bridge</span></div>}
 </div>
}
