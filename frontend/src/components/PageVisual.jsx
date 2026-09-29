const IMAGES={
 dashboard:new URL('../assets/banner_dashboard.webp', import.meta.url).href,
 schemes:new URL('../assets/banner_schemes.webp', import.meta.url).href,
 compare:new URL('../assets/banner_compare.webp', import.meta.url).href,
 calculator:new URL('../assets/banner_calculator.webp', import.meta.url).href,
 partners:new URL('../assets/banner_partners.webp', import.meta.url).href,
 documents:new URL('../assets/banner_documents.webp', import.meta.url).href,
 roadmap:new URL('../assets/banner_roadmap.webp', import.meta.url).href,
 profile:new URL('../assets/banner_profile.webp', import.meta.url).href,
 details:new URL('../assets/banner_details.webp', import.meta.url).href,
};
export default function PageVisual({kind,label,children}){const src=IMAGES[kind]||IMAGES.dashboard;return <div className="page-visual"><img src={src} alt=""/><div className="page-visual-overlay"><span>{label}</span>{children&&<strong>{children}</strong>}</div></div>}
