# 📱 Tech Guilds — Mobile App (Flutter)

Aplicativo móvel multiplataforma (**Android** e **iOS**) do **Tech Guilds**, desenvolvido em **Flutter** e orquestrado no **Monorepo Nx**.

---

## 🚀 Como Executar

### Pré-requisitos
- [Flutter SDK](https://docs.flutter.dev/get-started/install) instalado.
- Android Studio (com emulador Android) ou Xcode (para simulador iOS).

### Comandos Nx:
```bash
# Executar no dispositivo ou emulador conectado
npx nx serve mobile

# Executar testes do app
npx nx test mobile

# Gerar build APK de produção para Android
npx nx build mobile
```

---

## 🌐 Conexão com os Microsserviços

O app consome a malha de microsserviços via **API Gateway**:
- **Emulador Android:** `http://10.0.2.2:8000`
- **Simulador iOS / Dispositivo Real:** `http://localhost:8000` ou IP da sua rede local.
