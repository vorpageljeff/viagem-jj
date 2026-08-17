"use client";
import {useEffect} from "react";
import {useRouter} from "next/navigation";
export default function Home(){const router=useRouter();useEffect(()=>router.replace(localStorage.getItem("trip_token")?"/app":"/login"),[router]);return <main className="splash"><div className="brand-mark">B</div><p>Preparando sua viagem…</p></main>}
