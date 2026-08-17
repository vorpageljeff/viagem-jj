import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata={title:"Bora! • Garopaba 2027",description:"Gestão simples para viagens em grupo"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="pt-BR"><body>{children}</body></html>}

