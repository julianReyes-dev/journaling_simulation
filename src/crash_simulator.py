import json
import time
import random
from typing import List, Dict, Any
from .virtual_disk import VirtualDisk
from .journaling_fs import JournalingFileSystem, JournalEntryType

class CrashSimulator:
    """
    Simula fallos del sistema y cortes de energía
    """
    
    def __init__(self, disk: VirtualDisk, fs: JournalingFileSystem):
        self.disk = disk
        self.fs = fs
        self.crash_points = []
        
    def simulate_operation_sequence(self, operations: int, crash_probability: float = 0.3):
        """
        Simula una secuencia de operaciones con posibilidad de fallo
        """
        print(f"Iniciando simulación de {operations} operaciones...")
        print(f"Probabilidad de fallo: {crash_probability*100}%")
        
        successful_operations = 0
        
        for i in range(operations):
            # Simular diferentes tipos de operaciones
            op_type = random.choice(["create", "create", "create", "write"])  # Más creación
            
            try:
                if op_type == "create":
                    filename = f"test_file_{i}.dat"
                    # Archivos más grandes para usar más bloques
                    file_size = random.randint(3000, 7000)  # Aumentamos el tamaño
                    file_data = f"Datos de prueba para archivo {i} ".encode() * (file_size // 30)
                    success = self.fs.create_file(filename, file_data)
                    
                    if success:
                        successful_operations += 1
                        print(f"Operación {i+1}: Archivo '{filename}' creado ({len(file_data)} bytes)")
                    else:
                        print(f"Operación {i+1}: Falló creación de '{filename}'")
                        
                # Simular posible fallo del sistema
                if random.random() < crash_probability:
                    print(f"\nFALLO DEL SISTEMA SIMULADO en operación {i+1}")
                    # Corrupción MUY ligera para permitir recuperación
                    self.simulate_crash(corruption_level=0.02)  # Solo 2% de corrupción
                    break
                    
                # Pequeña pausa entre operaciones para mejor visualización
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error crítico en operación {i+1}: {e}")
                break
        
        print(f"\nSimulación completada: {successful_operations}/{operations} operaciones exitosas")
        return successful_operations
    
    def simulate_crash(self, corruption_level: float = 0.02):  # Solo 2% por defecto
        """
        Simula un fallo del sistema corruptiendo algunos bloques
        """
        total_blocks = self.disk.total_blocks
        
        # Encontrar bloques USED
        used_blocks = [i for i, status in enumerate(self.disk.block_status) 
                      if status.name == "USED"]
        
        if not used_blocks:
            print("No hay bloques usados para corromper")
            return
            
        # Calcular cuántos bloques corromper basado en los bloques USED, no totales
        blocks_to_corrupt = max(1, min(3, int(len(used_blocks) * corruption_level * 5)))  # Más conservador
        
        print(f"Corrompiendo {blocks_to_corrupt} de {len(used_blocks)} bloques usados...")
        
        # Seleccionar bloques USED aleatorios para corromper
        corrupted_blocks = random.sample(used_blocks, min(blocks_to_corrupt, len(used_blocks)))
        
        for block_num in corrupted_blocks:
            self.disk.mark_corrupted(block_num)
            
        print(f"Fallo simulado: {len(corrupted_blocks)} bloques de datos corruptos")
        
        # Información útil para debugging
        total_used = len(used_blocks)
        corruption_percentage = (len(corrupted_blocks) / total_used * 100) if total_used > 0 else 0
        print(f"Estadísticas: {corruption_percentage:.1f}% de bloques usados afectados")
        
        # Información sobre archivos afectados
        affected_inodes = set()
        for inode_id, inode in self.disk.inodes.items():
            for block_num in corrupted_blocks:
                if block_num in inode.blocks:
                    affected_inodes.add(inode_id)
                    break
        
        print(f"Archivos potencialmente afectados: {len(affected_inodes)}")
    
    def controlled_crash_during_operation(self, filename: str = "critical_operation.dat"):
        """
        Simula un fallo controlado durante una operación específica
        """
        print("Iniciando operación con fallo controlado...")
        
        # Fase 1: Iniciar operación crítica
        transaction_id = self.fs.begin_transaction()
        # Archivo más grande para usar múltiples bloques
        test_data = b"Critical operation data that might be interrupted by system crash " * 80
        
        if self.fs.journal_enabled:
            self.fs.journal_operation(
                JournalEntryType.FILE_CREATE,
                {
                    "filename": filename,
                    "size": len(test_data),
                    "data_checksum": self.fs.disk.calculate_checksum(test_data),
                    "transaction_id": transaction_id
                }
            )
            print("Journal actualizado - operación registrada")
        
        # Simular fallo justo después del journaling pero antes de completar la operación
        print("FALLO CONTROLADO: Sistema interrumpido durante ejecución")
        # Muy poca corrupción para el demo controlado - solo 1 bloque
        self.simulate_crash(corruption_level=0.01)  # Solo 1% de corrupción
        
        print("Operación interrumpida - lista para recuperación")
        return transaction_id
    
    def get_crash_statistics(self) -> Dict[str, any]:
        """Estadísticas de los fallos simulados"""
        total_blocks = self.disk.total_blocks
        corrupted_blocks = sum(1 for s in self.disk.block_status if s.name == "CORRUPTED")
        used_blocks = sum(1 for s in self.disk.block_status if s.name == "USED")
        
        return {
            "total_blocks": total_blocks,
            "used_blocks": used_blocks,
            "corrupted_blocks": corrupted_blocks,
            "corruption_rate_total": (corrupted_blocks / total_blocks * 100) if total_blocks > 0 else 0,
            "corruption_rate_used": (corrupted_blocks / used_blocks * 100) if used_blocks > 0 else 0,
            "crash_points_recorded": len(self.crash_points)
        }