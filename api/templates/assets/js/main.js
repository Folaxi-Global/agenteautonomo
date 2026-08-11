function simularPagoPro() {
    const btn = document.querySelector('.pricing-card button');
    btn.innerText = "Procesando Pasarela...";
    btn.style.opacity = "0.7";
    
    setTimeout(() => {
        alert("¡Transacción simulada con éxito! El Webhook ha actualizado la tesorería y el proyecto se marcó como exitoso en Supabase.");
        btn.innerText = "¡Suscripción Activa!";
        btn.style.background = "#238636";
    }, 1200);
}
