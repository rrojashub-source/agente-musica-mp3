# 🛠️ Tools Directory

Esta carpeta contiene herramientas externas necesarias para funcionalidades avanzadas.

---

## 📥 fpcalc.exe (Chromaprint)

**Status:** ⏳ Pendiente de instalación

**Propósito:**
- Audio fingerprinting para identificación de canciones
- Usado por AcoustID para matching preciso (95-100%)
- Similar a Shazam pero integrado en NEXUS

### Descarga e Instalación:

1. **Descarga Chromaprint:**
   - Ve a: https://acoustid.org/chromaprint
   - Descarga: `chromaprint-fpcalc-1.5.1-windows-x86_64.zip`

2. **Extrae el archivo:**
   - Descomprime el ZIP
   - Encontrarás `fpcalc.exe`

3. **Copia a este directorio:**
   ```
   AGENTE_MUSICA_MP3/tools/fpcalc.exe
   ```

4. **Verifica la instalación:**
   - Ejecuta: `fpcalc.exe -version`
   - Deberías ver: `fpcalc version 1.5.1`

### Uso en NEXUS:

Una vez instalado, NEXUS podrá:
- ✅ Analizar audio de MP3 para generar fingerprints
- ✅ Buscar matches en base de datos AcoustID
- ✅ Identificar canciones sin metadata
- ✅ Obtener metadata correcta desde MusicBrainz

### Troubleshooting:

**Error:** "fpcalc not found"
- Verifica que el archivo esté en `tools/fpcalc.exe`
- Verifica permisos de ejecución
- Reinicia la aplicación

**Error:** "missing DLL"
- Descarga el paquete completo (no solo fpcalc.exe)
- Copia todas las DLLs junto con fpcalc.exe

---

## 📝 Notas:

- Este archivo NO se incluye en Git (.gitignore)
- Cada usuario debe descargar su propia copia
- Tamaño aproximado: ~2 MB
- Licencia: MIT (open source)
