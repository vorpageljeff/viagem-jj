"use client";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { login } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@viagem.com");
  const [password, setPassword] = useState("viagem2026");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      await login(email, password);
      router.push("/app");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Falha ao entrar");
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
          <span className="eyebrow light">GAROPABA • VERÃO 2027</span>
          <h1>Todo mundo na mesma viagem.</h1>
          <p>
            Casas, votos, despesas e pagamentos organizados sem planilha no
            grupo.
          </p>
          <div className="trip-pill">
            <span>26 DEZ</span>
            <i />8 dias no litoral
            <i />
            <span>03 JAN</span>
          </div>
        </div>
        <small>Garopaba, Santa Catarina</small>
      </section>
      <section className="login-panel">
        <div className="login-box">
          <div className="brand mobile-brand">
            <span className="brand-mark">B</span>
            <span>Bora!</span>
          </div>
          <span className="eyebrow">ÁREA DO VIAJANTE</span>
          <h2>Que bom ter você aqui</h2>
          <p className="muted">
            Entre para acompanhar os próximos passos da viagem.
          </p>
          <form onSubmit={submit}>
            <label>
              E-mail
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </label>
            <label>
              Senha
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </label>
            {error && <div className="form-error">{error}</div>}
            <button className="primary full" disabled={loading}>
              {loading ? "Entrando…" : "Entrar na viagem →"}
            </button>
          </form>
          <div className="demo-note">
            <strong>Acesso de demonstração</strong>
            <span>admin@viagem.com · viagem2026</span>
          </div>
        </div>
      </section>
    </main>
  );
}
