import random
import time
from typing import List
from .virtual_disk import VirtualDisk
from .journaling_fs import JournalingFileSystem

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
                    file_size = random.randint(100, 5000)  # Tamaño aleatorio
                    file_data = f"Datos de prueba para archivo {i} ".encode() * (file_size // 50)
                    success = self.fs.create_file(filename, file_data)
                    
                    if success:
                        successful_operations += 1
                        print(f"Operación {i+1}: Archivo '{filename}' creado ({len(file_data)} bytes)")
                    else:
                        print(f"Operación {i+1}: Falló creación de '{filename}'")
                        
                # Simular posible fallo del sistema
                if random.random() < crash_probability:
                    print(f"\nFALLO DEL SISTEMA SIMULADO en operación {i+1}")
                    self.simulate_crash()
                    break
                    
                # Pequeña pausa entre operaciones para mejor visualización
                time.sleep(0.1)
                
            except Exception as e:
                print(f"Error crítico en operación {i+1}: {e}")
                break
        
        print(f"\n📈 Simulación completada: {successful_operations}/{operations} operaciones exitosas")
        return successful_operations
    
    def simulate_crash(self, corruption_level: float = 0.2):
        """
        Simula un fallo del sistema corruptiendo algunos bloques
        """
        total_blocks = self.disk.total_blocks
        blocks_to_corrupt = max(1, int(total_blocks * corruption_level))
        
        print(f"Corrompiendo {blocks_to_corrupt} bloques de {total_blocks}...")
        
        # Seleccionar bloques USED aleatorios para corromper
        used_blocks = [i for i, status in enumerate(self.disk.block_status) 
                      if status.name == "USED"]
        
        if used_blocks:
            corrupted_blocks = random.sample(used_blocks, min(blocks_to_corrupt, len(used_blocks)))
            
            for block_num in corrupted_blocks:
                self.disk.mark_corrupted(block_num)
                
            print(f"Fallo simulado: {len(corrupted_blocks)} bloques de datos corruptos")
        else:
            print("No hay bloques usados para corromper")
    
    def controlled_crash_during_operation(self, filename: str = "critical_operation.dat"):
        """
        Simula un fallo controlado durante una operación específica
        """
        print("Iniciando operación con fallo controlado...")
        
        # Fase 1: Iniciar operación crítica
        transaction_id = self.fs.begin_transaction()
        test_data = b"Critical operation data that might be interrupted by system crash"
        
        # Registrar en journal (Fase de journaling completada)
        if self.fs.journal_enabled:
            self.fs.journal_operation(
                self.fs.JournalEntryType.FILE_CREATE,
                {
                    "filename": filename,
                    "size": len(test_data),
                    "data_checksum": self.fs.disk.calculate_checksum(test_data),
                    "transaction_id": transaction_id
                }
            )
            print("📝 Journal actualizado - operación registrada")
        
        # Simular fallo justo después del journaling pero antes de completar la operación
        print("FALLO CONTROLADO: Sistema interrumpido durante ejecución")
        self.simulate_crash(correlation_level=0.15)
        
        print("🔄 Operación interrumpida - lista para recuperación")
        return transaction_id
    
    def get_crash_statistics(self) -> Dict[str, any]:
        """Estadísticas de los fallos simulados"""
        total_blocks = self.disk.total_blocks
        corrupted_blocks = sum(1 for s in self.disk.block_status if s.name == "CORRUPTED")
        
        return {
            "total_blocks": total_blocks,
            "corrupted_blocks": corrupted_blocks,
            "corruption_rate": (corrupted_blocks / total_blocks * 100) if total_blocks > 0 else 0,
            "crash_points_recorded": len(self.crash_points)
        }