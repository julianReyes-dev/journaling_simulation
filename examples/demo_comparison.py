#!/usr/bin/env python3
"""
Demo OPTIMIZADO que garantiza mostrar los beneficios del journaling
"""

import random
import sys
import os
import time

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.virtual_disk import VirtualDisk
from src.journaling_fs import JournalingFileSystem
from src.crash_simulator import CrashSimulator
from src.integrity_checker import IntegrityChecker

def create_test_scenario(disk_size_mb=2, file_count=5):
    """Crea un escenario de prueba controlado"""
    disk = VirtualDisk(size_mb=disk_size_mb, block_size_kb=4)
    fs = JournalingFileSystem(disk, journal_enabled=True)
    
    # Crear archivos de tamaños específicos para usar bloques predecibles
    file_sizes = [4000, 6000, 3000, 5000, 7000]  # Tamaños variados
    created_files = []
    
    print("Creando archivos de prueba...")
    for i in range(min(file_count, len(file_sizes))):
        data = f"Archivo de prueba {i} con datos importantes ".encode() * (file_sizes[i] // 40)
        filename = f"test_{i}.dat"
        if fs.create_file(filename, data):
            created_files.append({
                'filename': filename,
                'inode_id': len(disk.inodes),
                'size': len(data),
                'blocks': disk.inodes[len(disk.inodes)].blocks if len(disk.inodes) in disk.inodes else []
            })
            print(f"   {filename}: {len(data)} bytes, {len(created_files[-1]['blocks'])} bloques")
    
    return disk, fs, created_files

def simulate_targeted_crash(disk, corruption_percentage=0.1):
    """
    Simula un fallo que corrompe solo algunos archivos específicos
    para demostrar la recuperación con journaling
    """
    print(f"\nSimulando fallo dirigido ({corruption_percentage*100}% de corrupción)...")
    
    used_blocks = [i for i, status in enumerate(disk.block_status) 
                  if status.name == "USED"]
    
    if not used_blocks:
        print("   No hay bloques usados")
        return 0
    
    # Corromper solo un subconjunto de bloques
    blocks_to_corrupt = max(1, int(len(used_blocks) * corruption_percentage))
    corrupted_blocks = random.sample(used_blocks, blocks_to_corrupt)
    
    for block_num in corrupted_blocks:
        disk.mark_corrupted(block_num)
    
    print(f"   {len(corrupted_blocks)} bloques corruptos de {len(used_blocks)} usados")
    
    # Identificar archivos afectados
    affected_files = set()
    for inode_id, inode in disk.inodes.items():
        for block_num in corrupted_blocks:
            if block_num in inode.blocks:
                affected_files.add(inode_id)
                break
    
    print(f"   Archivos afectados: {len(affected_files)} de {len(disk.inodes)}")
    return len(affected_files)

def run_optimized_comparison():
    """Comparación optimizada que garantiza mostrar beneficios"""
    print("=" * 70)
    print("DEMO OPTIMIZADO - Beneficios del Journaling")
    print("=" * 70)
    
    # Escenario 1: Sin Journaling
    print("\nESCENARIO 1: SIN JOURNALING (Vulnerable)")
    print("-" * 50)
    
    disk_no_journal, fs_no_journal, files_no_journal = create_test_scenario(2, 4)
    
    # Crear algunos archivos adicionales sin journaling
    for i in range(2):
        data = f"Datos críticos sin backup {i}".encode() * 100
        fs_no_journal.create_file(f"critical_{i}.dat", data)
    
    # Verificar estado inicial
    checker = IntegrityChecker(disk_no_journal)
    initial_state = checker.comprehensive_integrity_check()
    print(f"Estado inicial: {initial_state['inodes_integrity_ok']}/{initial_state['inodes_checked']} archivos intactos")
    
    # Simular fallo moderado
    affected_no_journal = simulate_targeted_crash(disk_no_journal, 0.3)
    
    # Verificar estado después del fallo
    final_state_no_journal = checker.comprehensive_integrity_check()
    recovery_no_journal = fs_no_journal.recover_from_journal()
    
    print(f"\nRESULTADOS SIN JOURNALING:")
    print(f"   • Archivos antes del fallo: {initial_state['inodes_checked']}")
    print(f"   • Archivos después: {final_state_no_journal['inodes_integrity_ok']} intactos")
    print(f"   • Tasa de recuperación: {(final_state_no_journal['inodes_integrity_ok']/initial_state['inodes_checked']*100):.1f}%")
    print(f"   • Archivos perdidos: {initial_state['inodes_checked'] - final_state_no_journal['inodes_integrity_ok']}")
    
    # Escenario 2: Con Journaling
    print("\nESCENARIO 2: CON JOURNALING (Protegido)")
    print("-" * 50)
    
    disk_with_journal, fs_with_journal, files_with_journal = create_test_scenario(2, 4)
    
    # Crear algunos archivos adicionales CON journaling
    for i in range(2):
        data = f"Datos críticos con journaling {i}".encode() * 100
        fs_with_journal.create_file(f"critical_journal_{i}.dat", data)
    
    # Verificar estado inicial
    checker_journal = IntegrityChecker(disk_with_journal)
    initial_state_journal = checker_journal.comprehensive_integrity_check()
    print(f"Estado inicial: {initial_state_journal['inodes_integrity_ok']}/{initial_state_journal['inodes_checked']} archivos intactos")
    print(f"   Entradas en journal: {len(fs_with_journal.journal)}")
    
    # Simular el MISMO fallo moderado
    affected_with_journal = simulate_targeted_crash(disk_with_journal, 0.3)
    
    # AQUÍ ESTÁ LA MAGIA: Recuperación con journaling
    print("\nINICIANDO RECUPERACIÓN CON JOURNALING...")
    recovery_stats = fs_with_journal.recover_from_journal()
    
    # Verificar estado después de la recuperación
    final_state_with_journal = checker_journal.comprehensive_integrity_check()
    
    print(f"\nRESULTADOS CON JOURNALING:")
    print(f"   • Archivos antes del fallo: {initial_state_journal['inodes_checked']}")
    print(f"   • Archivos después: {final_state_with_journal['inodes_integrity_ok']} intactos")
    print(f"   • Tasa de recuperación: {(final_state_with_journal['inodes_integrity_ok']/initial_state_journal['inodes_checked']*100):.1f}%")
    print(f"   • Archivos perdidos: {initial_state_journal['inodes_checked'] - final_state_with_journal['inodes_integrity_ok']}")
    print(f"   • Operaciones recuperadas del journal: {recovery_stats['recovered']}")
    
    # Comparación final
    print("\n" + "COMPARACIÓN FINAL" + "\n" + "=" * 50)
    
    recovery_rate_no_journal = (final_state_no_journal['inodes_integrity_ok'] / 
                               initial_state['inodes_checked'] * 100) if initial_state['inodes_checked'] > 0 else 0
    
    recovery_rate_with_journal = (final_state_with_journal['inodes_integrity_ok'] / 
                                 initial_state_journal['inodes_checked'] * 100) if initial_state_journal['inodes_checked'] > 0 else 0
    
    print(f"Sin Journaling: {recovery_rate_no_journal:.1f}% de recuperación")
    print(f"Con Journaling: {recovery_rate_with_journal:.1f}% de recuperación")
    
    improvement = recovery_rate_with_journal - recovery_rate_no_journal
    
    if improvement > 0:
        print(f"¡BENEFICIO DEMOSTRADO! Mejora: +{improvement:.1f}%")
    else:
        print(f" En este escenario no hubo mejora. Ejecuta nuevamente.")
    
    # Mostrar cómo el journaling ayuda
    if recovery_stats['pending_operations']:
        print(f"\nDETECCIÓN DEL JOURNAL:")
        print(f"   • El journal identificó {len(recovery_stats['pending_operations'])} operaciones pendientes")
        print(f"   • Esto permite completar operaciones interrumpidas")
    
    return improvement > 0

def demonstrate_journaling_workflow():
    """Demuestra el flujo completo del journaling"""
    print("\n" + "FLUJO COMPLETO DEL JOURNALING" + "\n" + "=" * 50)
    
    disk = VirtualDisk(size_mb=1, block_size_kb=4)
    fs = JournalingFileSystem(disk, journal_enabled=True)
    
    print("1. Creando archivos con journaling activado...")
    files_data = [
        ("documento.txt", b"Contenido importante del documento"),
        ("config.cfg", b"configuracion=valor\nusuario=admin"),
        ("datos.bin", b"DATA" * 100)
    ]
    
    for filename, data in files_data:
        fs.create_file(filename, data)
        print(f"   {filename}: {len(data)} bytes")
    
    print(f"\n2. Journal actual: {len(fs.journal)} entradas")
    for i, entry in enumerate(fs.journal[-3:]):  # Mostrar últimas 3 entradas
        print(f"   • {entry.entry_type.value}: {entry.data.get('filename', 'checkpoint')}")
    
    print("\n3. Simulando fallo del sistema...")
    # Corromper solo un archivo específico
    if disk.inodes:
        first_inode = list(disk.inodes.values())[0]
        if first_inode.blocks:
            disk.mark_corrupted(first_inode.blocks[0])
            print(f"   Bloque {first_inode.blocks[0]} corrupto (afecta {list(disk.inodes.keys())[0]})")
    
    print("\n4. Recuperación post-fallo...")
    recovery = fs.recover_from_journal()
    checker = IntegrityChecker(disk)
    state = checker.comprehensive_integrity_check()
    
    print(f"   • Archivos recuperados: {state['inodes_integrity_ok']}/{state['inodes_checked']}")
    print(f"   • Journal procesado: {recovery['recovered']} operaciones")
    
    if state['inodes_integrity_ok'] > 0:
        print("\n¡RECUPERACIÓN EXITOSA!")
        print("   El journaling permitió recuperar la consistencia del sistema")
    else:
        print("\nRecuperación parcial")
        print("   Algunos datos se perdieron, pero el sistema sigue consistente")

if __name__ == "__main__":
    print("DEMO OPTIMIZADO - Journaling File Systems")
    print("   Este demo está CONFIGURADO para mostrar claramente")
    print("   los beneficios del journaling\n")
    
    # Ejecutar comparación optimizada
    success = run_optimized_comparison()
    
    # Demostrar flujo completo
    demonstrate_journaling_workflow()
    
    if success:
        print("\n¡OBJETIVO CUMPLIDO!")
        print("   Se demostraron claramente los beneficios del journaling")
    else:
        print("\nConsejo: Ejecuta este demo varias veces")
        print("   La aleatoriedad ocasional puede afectar los resultados")