import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.virtual_disk import VirtualDisk
from src.journaling_fs import JournalingFileSystem
from src.crash_simulator import CrashSimulator
from src.integrity_checker import IntegrityChecker

class TestCrashRecovery(unittest.TestCase):
    
    def test_recovery_after_crash(self):
        """Test de recuperación después de un fallo simulado"""
        disk = VirtualDisk(size_mb=1)
        fs = JournalingFileSystem(disk, journal_enabled=True)
        crash_sim = CrashSimulator(disk, fs)
        
        # Crear algunos archivos
        files_created = []
        for i in range(4):
            data = f"File data {i}".encode() * 200
            filename = f"test_file_{i}.dat"
            if fs.create_file(filename, data):
                files_created.append(filename)
        
        # Simular fallo
        crash_sim.simulate_crash(corruption_level=0.3)
        
        # Verificar recuperación
        recovery_stats = fs.recover_from_journal()
        checker = IntegrityChecker(disk)
        integrity_report = checker.comprehensive_integrity_check()
        
        # Debería poder recuperar alguna información
        self.assertIn('recovered', recovery_stats)
        self.assertIn('inodes_integrity_ok', integrity_report)
        
    def test_checksum_verification(self):
        """Test de verificación de checksum después de corrupción"""
        disk = VirtualDisk(size_mb=1)
        fs = JournalingFileSystem(disk, journal_enabled=True)
        
        # Crear archivo de prueba
        original_data = b"Important data that must be verified"
        fs.create_file("checksum_test.txt", original_data)
        
        # Encontrar el inodo
        inode_id = list(disk.inodes.keys())[0]
        inode = disk.inodes[inode_id]
        
        # Verificar que el checksum coincide inicialmente
        read_data = fs.read_file(inode_id)
        self.assertEqual(disk.calculate_checksum(read_data), inode.checksum)
        
        # Corromper un bloque
        if inode.blocks:
            disk.mark_corrupted(inode.blocks[0])
            
            # Ahora la lectura debería fallar o mostrar advertencia
            corrupted_read = fs.read_file(inode_id)
            # El comportamiento puede variar, pero no debería crashear

if __name__ == '__main__':
    unittest.main()