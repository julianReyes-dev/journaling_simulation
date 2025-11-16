#!/usr/bin/env python3
"""
Demo que compara sistemas de archivos con y sin journaling
ante fallos del sistema
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.virtual_disk import VirtualDisk
from src.journaling_fs import JournalingFileSystem
from src.crash_simulator import CrashSimulator
from src.integrity_checker import IntegrityChecker

def run_comparison():
    """Ejecuta comparación entre FS con y sin journaling"""
    
    print("=" * 70)
    print("COMPARACIÓN: Sistemas de Archivos con vs sin Journaling")
    print("=" * 70)
    
    # Configuración - menos operaciones para demo más rápida y clara
    operations = 10
    crash_probability = 0.3  # Mayor probabilidad para ver más fallos
    
    # Caso 1: Sin journaling
    print("\n" + "CASO 1: SISTEMA SIN JOURNALING" + "\n" + "-" * 50)
    
    disk_no_journal = VirtualDisk(size_mb=2)  # Disco más pequeño para demo rápida
    fs_no_journal = JournalingFileSystem(disk_no_journal, journal_enabled=False)
    crash_sim_no_journal = CrashSimulator(disk_no_journal, fs_no_journal)
    checker_no_journal = IntegrityChecker(disk_no_journal)
    
    # Ejecutar operaciones con fallo simulado
    successful_ops_no_journal = crash_sim_no_journal.simulate_operation_sequence(
        operations=operations, 
        crash_probability=crash_probability
    )
    
    # Verificar integridad después del fallo
    final_state_no_journal = checker_no_journal.comprehensive_integrity_check()
    recovery_no_journal = fs_no_journal.recover_from_journal()
    
    print(f"\nRESULTADOS SIN JOURNALING:")
    print(f"   • Operaciones exitosas: {successful_ops_no_journal}/{operations}")
    print(f"   • Archivos intactos: {final_state_no_journal['inodes_integrity_ok']}/{final_state_no_journal['inodes_checked']}")
    print(f"   • Bloques corruptos: {final_state_no_journal['corrupted_blocks']}")
    print(f"   • Operaciones recuperadas: {recovery_no_journal['recovered']}")
    
    # Mostrar reporte detallado
    checker_no_journal.print_detailed_report(final_state_no_journal)
    
    # Caso 2: Con journaling
    print("\n" + "CASO 2: SISTEMA CON JOURNALING" + "\n" + "-" * 50)
    
    disk_with_journal = VirtualDisk(size_mb=2)
    fs_with_journal = JournalingFileSystem(disk_with_journal, journal_enabled=True)
    crash_sim_with_journal = CrashSimulator(disk_with_journal, fs_with_journal)
    checker_with_journal = IntegrityChecker(disk_with_journal)
    
    # Ejecutar operaciones con fallo simulado
    successful_ops_with_journal = crash_sim_with_journal.simulate_operation_sequence(
        operations=operations, 
        crash_probability=crash_probability
    )
    
    # Estado después del fallo + recuperación
    final_state_with_journal = checker_with_journal.comprehensive_integrity_check()
    recovery_with_journal = fs_with_journal.recover_from_journal()
    
    print(f"\nRESULTADOS CON JOURNALING:")
    print(f"   • Operaciones exitosas: {successful_ops_with_journal}/{operations}")
    print(f"   • Archivos intactos: {final_state_with_journal['inodes_integrity_ok']}/{final_state_with_journal['inodes_checked']}")
    print(f"   • Bloques corruptos: {final_state_with_journal['corrupted_blocks']}")
    print(f"   • Operaciones recuperadas: {recovery_with_journal['recovered']}")
    print(f"   • Entradas en journal: {len(fs_with_journal.journal)}")
    
    # Mostrar reporte detallado
    checker_with_journal.print_detailed_report(final_state_with_journal)
    
    # Comparación final
    print("\n" + "COMPARACIÓN FINAL" + "\n" + "=" * 50)
    
    recovery_rate_no_journal = (final_state_no_journal['inodes_integrity_ok'] / 
                               final_state_no_journal['inodes_checked'] * 100 
                               if final_state_no_journal['inodes_checked'] > 0 else 0)
    
    recovery_rate_with_journal = (final_state_with_journal['inodes_integrity_ok'] / 
                                 final_state_with_journal['inodes_checked'] * 100 
                                 if final_state_with_journal['inodes_checked'] > 0 else 0)
    
    print(f"Sin Journaling:")
    print(f"   • Tasa de recuperación: {recovery_rate_no_journal:.1f}%")
    print(f"   • Archivos perdidos: {len(final_state_no_journal['corrupted_files'])}")
    print(f"   • Eficiencia: {successful_ops_no_journal/operations*100:.1f}%")
    
    print(f"Con Journaling:")
    print(f"   • Tasa de recuperación: {recovery_rate_with_journal:.1f}%")
    print(f"   • Archivos perdidos: {len(final_state_with_journal['corrupted_files'])}")
    print(f"   • Eficiencia: {successful_ops_with_journal/operations*100:.1f}%")
    
    improvement = recovery_rate_with_journal - recovery_rate_no_journal
    print(f"Mejora con Journaling: +{improvement:.1f}% en tasa de recuperación")
    
    # Estadísticas del journal
    journal_stats = fs_with_journal.get_journal_stats()
    print(f"\nESTADÍSTICAS DEL JOURNAL:")
    print(f"   • Total entradas: {journal_stats['total_entries']}")
    for entry_type, count in journal_stats['entry_types'].items():
        print(f"   • {entry_type}: {count}")
    
    # Conclusión
    print("\n" + "CONCLUSIÓN" + "\n" + "=" * 50)
    if improvement > 10:
        print("El journaling demostró una mejora significativa en la")
        print("   recuperación de datos después de fallos del sistema.")
    elif improvement > 0:
        print("El journaling mostró una mejora moderada en la")
        print("   recuperación de datos.")
    else:
        print("En esta ejecución, los resultados fueron similares.")
        print("   Ejecuta nuevamente para ver la mejora típica.")
        print("   (La aleatoriedad puede afectar los resultados)")
    
    return {
        "without_journaling": {
            "recovery_rate": recovery_rate_no_journal,
            "files_lost": len(final_state_no_journal['corrupted_files']),
            "efficiency": successful_ops_no_journal/operations*100
        },
        "with_journaling": {
            "recovery_rate": recovery_rate_with_journal,
            "files_lost": len(final_state_with_journal['corrupted_files']),
            "efficiency": successful_ops_with_journal/operations*100
        }
    }

def run_controlled_crash_demo():
    """Demo con fallo controlado para mostrar recuperación específica"""
    print("\n" + "DEMO: FALLO CONTROLADO CON RECUPERACIÓN" + "\n" + "=" * 50)
    
    disk = VirtualDisk(size_mb=1)
    fs = JournalingFileSystem(disk, journal_enabled=True)
    crash_sim = CrashSimulator(disk, fs)
    checker = IntegrityChecker(disk)
    
    # Crear algunos archivos primero
    print("Creando archivos iniciales...")
    for i in range(3):
        data = f"Archivo inicial {i}".encode() * 50
        fs.create_file(f"init_{i}.txt", data)
    
    # Verificar estado inicial
    print("\nESTADO INICIAL:")
    initial_check = checker.comprehensive_integrity_check()
    print(f"   • Archivos creados: {initial_check['inodes_checked']}")
    print(f"   • Todos intactos: {initial_check['inodes_integrity_ok'] == initial_check['inodes_checked']}")
    
    # Simular fallo controlado durante operación crítica
    print("\nSimulando fallo durante operación crítica...")
    transaction_id = crash_sim.controlled_crash_during_operation("archivo_critico.dat")
    
    print("\nPROCESO DE RECUPERACIÓN:")
    recovery_stats = fs.recover_from_journal()
    integrity_after = checker.comprehensive_integrity_check()
    
    print(f"\nResultados recuperación:")
    print(f"   • Operaciones recuperadas: {recovery_stats['recovered']}")
    print(f"   • Errores: {recovery_stats['errors']}")
    print(f"   • Operaciones pendientes: {len(recovery_stats['pending_operations'])}")
    
    checker.print_detailed_report(integrity_after)
    
    # Mostrar qué archivos sobrevivieron
    surviving_files = [f for f in integrity_after['recoverable_files']]
    print(f"\nARCHIVOS QUE SOBREVIVIERON AL FALLO: {len(surviving_files)}")
    for file_info in surviving_files:
        print(f"   • Inodo {file_info['inode_id']}: {file_info['size']} bytes - {file_info['status']}")

if __name__ == "__main__":
    print("Iniciando demostración de Journaling File System")
    print("   Este demo comparará sistemas con y sin journaling")
    print("   ante fallos simulados del sistema.\n")
    
    # Ejecutar comparación principal
    results = run_comparison()
    
    # Ejecutar demo de fallo controlado
    run_controlled_crash_demo()
    
    print("\n" + "Demostración completada!")
    print("Tipsito :D : Ejecuta nuevamente para ver diferentes resultados")
    print("   (la aleatoriedad en los fallos produce variaciones)")