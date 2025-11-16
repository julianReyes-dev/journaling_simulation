# Journaling File System Simulation

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Descripción
Simulación educativa que demuestra cómo los sistemas de archivos con **journaling** (como ext3, ext4) protegen contra la pérdida de datos durante fallos del sistema mediante un mecanismo de registro transaccional.

## Objetivo
Comparar cuantitativamente el comportamiento de sistemas **con y sin journaling** ante fallos repentinos (cortes de energía, crashes del sistema).

## Características

### Módulos Principales
- **`VirtualDisk`**: Disco virtual con gestión de bloques e inodos
- **`JournalingFS`**: Sistema de archivos con journaling transaccional  
- **`CrashSimulator`**: Simulador de fallos del sistema
- **`IntegrityChecker`**: Verificador de integridad post-fallo

### Funcionalidades
- Simulación realista de operaciones de filesystem
- Mecanismo completo de journaling (write-ahead logging)
- Fallos del sistema con corrupción de datos
- Recuperación automática desde journal
- Verificación de integridad con checksums
- Comparación lado a lado con métricas
- Pruebas unitarias comprehensivas

## Ejecución Rápida

### Demo Principal (Recomendado)
```bash
# Ejecutar comparación completa con/sin journaling
python examples/demo_comparison.py
```

### Pruebas Unitarias
```bash
# Ejecutar todas las pruebas
python -m unittest discover tests

# Ejecutar pruebas específicas
python -m unittest tests/test_journaling.py
python -m unittest tests/test_crash_recovery.py
```

### Ejecución Individual de Módulos
```python
from src.virtual_disk import VirtualDisk
from src.journaling_fs import JournalingFileSystem
from src.crash_simulator import CrashSimulator
from src.integrity_checker import IntegrityChecker

# Configurar sistema
disk = VirtualDisk(size_mb=5)
fs = JournalingFileSystem(disk, journal_enabled=True)

# Usar el sistema...
fs.create_file("test.txt", b"Hello, Journaling!")
```

## Resultados Esperados

### Ejecución Típica del Demo
```
SIN JOURNALING:
   • Tasa de recuperación: 25-45%
   • Archivos perdidos: 4-8 de 15
   
CON JOURNALING:  
   • Tasa de recuperación: 75-95%
   • Archivos perdidos: 0-2 de 15
   
Mejora con Journaling: +40-60% en recuperación
```

### Métricas Clave
- **Tasa de Recuperación**: % de archivos intactos post-fallo
- **Archivos Perdidos**: Archivos corruptos o inconsistentes  
- **Eficiencia**: % de operaciones completadas exitosamente
- **Bloques Corruptos**: Número de bloques de datos dañados

## Estructura del Proyecto
```
journaling_simulation/
├── src/                    # Código fuente principal
│   ├── virtual_disk.py     # Gestión de almacenamiento
│   ├── journaling_fs.py    # Sistema de archivos + journaling
│   ├── crash_simulator.py  # Simulación de fallos
│   └── integrity_checker.py# Verificación post-fallo
├── tests/                  # Pruebas unitarias
│   ├── test_journaling.py
│   └── test_crash_recovery.py
├── examples/               # Demos y ejemplos
│   └── demo_comparison.py  # Demo principal
├── docs/                   # Documentación técnica
└── README.md
```

## Conceptos Teóricos Demostrados

### 1. Write-Ahead Logging (WAL)
Las operaciones se registran en el journal antes de ejecutarse en el disco principal.

### 2. Transacciones Atómicas
Cada operación es todo-o-nada, garantizando consistencia.

### 3. Recuperación Post-Caída
El sistema reconstruye el estado consistente examinando el journal.

### 4. Checkpoints Periódicos  
Limitan el tamaño del journal y aceleran la recuperación.

## Requisitos del Sistema

- **Python**: 3.8 o superior
- **Memoria**: 50 MB mínimo
- **Sistema Operativo**: Cualquier plataforma con Python

## Licencia
Este proyecto es con fines educativos. Licencia MIT.
Cada ejecución produce resultados ligeramente diferentes debido a la aleatoriedad en la simulación de fallos. Ejecuta múltiples veces para ver el rango típico de mejoras.

¡El proyecto está listo! Sigue los pasos en orden y tendrás un sistema completo de simulación de journaling file systems.
