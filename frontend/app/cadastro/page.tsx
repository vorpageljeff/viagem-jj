"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { registerAccount } from "@/lib/api";

export default function CadastroPage() {
  const router = useRouter();
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const form = new FormData(event.currentTarget);
    const password = String(form.get("password") || "");
    if (password !== String(form.get("password_confirmation") || "")) {
      setError("As senhas não coincidem");
      return;
    }
    setLoading(true);
    try {
      await registerAccount({
        name: String(form.get("name") || ""),
        email: String(form.get("email") || ""),
        phone: String(form.get("phone") || "") || undefined,
        password,
      });
      router.push("/app");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Não foi possível criar seu acesso");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <section className="login-story">
        <div className="brand light">
          <span className="brand-mark">B</span>
          <span>Bora!</span>
        </div>
        <div className="story-copy">
          <span className="eyebrow light">SEU ACESSO À VIAGEM</span>
          <h1>Participe das decisões do grupo.</h1>
          <p>Crie sua conta para organizar uma viagem ou participar das decisões do grupo.</p>
        </div>
        <small>Seu acesso, seus votos e seus pagamentos.</small>
      </section>
      <section className="login-panel">
        <div className="login-box">
          <div className="brand mobile-brand">
            <span className="brand-mark">B</span>
            <span>Bora!</span>
          </div>
          <span className="eyebrow">CRIAR CONTA</span>
          <h2>Ative seu acesso</h2>
          <p className="muted">Não é necessário convite para começar.</p>
          <form onSubmit={submit}>
            <label>Nome completo<input name="name" autoComplete="name" required minLength={2} /></label>
            <label>E-mail<input name="email" type="email" autoComplete="email" required /></label>
            <label>Telefone (opcional)<input name="phone" type="tel" autoComplete="tel" /></label>
            <label>Senha<input name="password" type="password" autoComplete="new-password" required minLength={8} maxLength={72} /></label>
            <label>Confirmar senha<input name="password_confirmation" type="password" autoComplete="new-password" required minLength={8} maxLength={72} /></label>
            {error && <div className="form-error">{error}</div>}
            <button className="primary full" disabled={loading}>
              {loading ? "Criando…" : "Criar meu acesso →"}
            </button>
          </form>
          <p className="auth-switch">Já possui conta? <Link href="/login">Entrar</Link></p>
        </div>
      </section>
    </main>
  );
}
