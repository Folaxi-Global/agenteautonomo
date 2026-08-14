import React, { useEffect, useState } from 'react';
import { createClient } from '@supabase/supabase-js';

// Inicializar cliente Supabase en el navegador
const supabase = createClient(
  import.meta.env.PUBLIC_SUPABASE_URL,
  import.meta.env.PUBLIC_SUPABASE_ANON_KEY
);

export default function AdminDashboard() {
  const [session, setSession] = useState(null);
  const [misProyectos, setMisProyectos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Verificar sesión activa al cargar
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      if (session) {
        fetchMisProyectos(session.user.email);
      } else {
        setLoading(false);
        // Redirigir a login si no hay sesión
        window.location.href = '/login';
      }
    });

    // Escuchar cambios de auth (login/logout)
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
      if (session) {
        fetchMisProyectos(session.user.email);
      } else {
        window.location.href = '/login';
      }
    });

    return () => subscription.unsubscribe();
  }, []);

  const fetchMisProyectos = async (email) => {
    setLoading(true);
    // Lógica: Obtener de Supabase los proyectos donde el 'email_cliente'
    // coincida con el usuario logueado.
    // Esto requiere una tabla 'clientes' o 'suscripciones' relacionada
    // con la tabla 'proyectos'.
    try {
      // EJEMPLO SIMPLIFICADO: Asumimos que existe una tabla 'suscripciones'
      // que vincula usuarios (email) con proyectos.
      const { data, error } = await supabase
        .from('suscripciones')
        .select(`
          id,
          estado,
          fecha_renovacion,
          proyectos (
            nombre_proyecto,
            subdominio,
            pais_objetivo
          )
        `)
        .eq('email_cliente', email);

      if (error) throw error;
      setMisProyectos(data || []);
    } catch (error) {
      console.error('Error fetching user projects:', error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  if (loading) {
    return <div className="flex justify-center py-20"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>;
  }

  if (!session) {
    return null; // O un mensaje de "redirigiendo"
  }

  return (
    <div className="py-16 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex justify-between items-center mb-10 pb-6 border-b border-gray-200">
          <h1 className="text-4xl font-extrabold text-gray-950 tracking-tight">Mi Cuenta Vartens</h1>
          <button onClick={handleLogout} className="px-4 py-2 text-sm text-gray-600 bg-gray-100 rounded-lg hover:bg-gray-200">
            Cerrar Sesión
          </button>
        </div>

        <div className="bg-white p-8 rounded-2xl border border-gray-100 shadow-sm">
          <h2 className="text-xl font-bold text-gray-800 mb-6">Mis Suscripciones Activas</h2>
          
          {misProyectos.length === 0 ? (
            <div className="text-center py-10 bg-gray-50 rounded-lg">
              <p className="text-gray-600">Aún no tienes suscripciones activas en el ecosistema Vartens.</p>
              <a href="/directorio" className="mt-4 inline-block text-blue-600 font-semibold hover:underline">Explorar soluciones</a>
            </div>
          ) : (
            <div className="space-y-6">
              {misProyectos.map((suscripcion) => (
                <div key={suscripcion.id} className="flex items-center justify-between p-6 border border-gray-200 rounded-xl hover:border-blue-200 transition">
                  <div>
                    <div className="flex items-center gap-3">
                        <span className="px-3 py-1 text-xs font-bold bg-green-50 text-green-700 rounded-full uppercase tracking-wider">
                            {s
