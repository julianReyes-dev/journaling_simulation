import unittest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.virtual_disk import VirtualDisk
from src.journaling_fs import JournalingFileSystem, JournalEntryType
from src.integrity_checker import IntegrityChecker

class TestJournalingFileSystem(unittest.TestCase):
    
    def setUp(self):
        """Configuración antes de cada test"""
        self.disk = VirtualDisk(size_mb=1)  # Disco pequeño para pruebas rápidas
        self.fs_with_journal = JournalingFileSystem(self.disk, journal_enabled=True)
        self.fs_no_journal = JournalingFileSystem(self.disk, journal_enabled=False)
        
    def test_file_creation_with_journal(self):
        """Test que verifica la creación de archivos con journaling"""
        test_data = b"Test data for journaling verification"
        success = self.fs_with_journal.create_file("test_journal.txt", test_data)
        
        self.assertTrue(success)
        self.assertGreater(len(self.fs_with_journal.journal), 0)
        
        # Verificar que se registró en el journal
        journal_entries = [e for e in self.fs_with_journal.journal 
                          if e.entry_type == JournalEntryType.FILE_CREATE]
        self.assertEqual(len(journal_entries), 1)
        
    def test_file_creation_without_journal(self):
        """Test que verifica creación sin journaling"""
        test_data = b"Test data without journaling"
        success = self.fs_no_journal.create_file("test_no_journal.txt", test_data)
        
        self.assertTrue(success)
        self.assertEqual(len(self.fs_no_journal.journal), 0)  # No debe haber entradas
        
    def test_file_read_integrity(self):
        """Test de lectura y verificación de integridad"""
        original_data = b"Original data for integrity test"
        self.fs_with_journal.create_file("integrity_test.txt", original_data)
        
        # Encontrar el inodo creado
        self.assertEqual(len(self.disk.inodes), 1)
        inode_id = list(self.disk.inodes.keys())[0]
        
        # Leer y verificar
        read_data = self.fs_with_journal.read_file(inode_id)
        self.assertEqual(read_data, original_data)
        
    def test_journal_recovery_mechanism(self):
        """Test del mecanismo de recuperación del journal"""
        # Realizar varias operaciones
        for i in range(3):
            data = f"File {i} data".encode()
            self.fs_with_journal.create_file(f"file_{i}.txt", data)
        
        # Simular recuperación después de fallo
        recovery_stats = self.fs_with_journal.recover_from_journal()
        
        # Verificar que el proceso de recuperación funciona
        self.assertIn('recovered', recovery_stats)
        self.assertIn('errors', recovery_stats)
        self.assertIn('pending_operations', recovery_stats)
        
    def test_disk_block_management(self):
        """Test de gestión de bloques del disco virtual"""
        # Verificar estado inicial
        stats = self.disk.get_disk_stats()
        self.assertEqual(stats['used_blocks'], 0)
        self.assertEqual(stats['free_blocks'], self.disk.total_blocks)
        
        # Escribir datos
        test_data = b"X" * 5000  # Ocupará múltiples bloques
        self.fs_with_journal.create_file("large_file.dat", test_data)
        
        # Verificar que se usaron bloques
        stats_after = self.disk.get_disk_stats()
        self.assertGreater(stats_after['used_blocks'], 0)
        
    def test_integrity_checker(self):
        """Test del verificador de integridad"""
        # Crear algunos archivos
        for i in range(2):
            data = f"Test file {i}".encode() * 100
            self.fs_with_journal.create_file(f"test_{i}.dat", data)
        
        # Ejecutar verificación
        checker = IntegrityChecker(self.disk)
        results = checker.comprehensive_integrity_check()
        
        # Verificar estructura del reporte
        self.assertIn('inodes_checked', results)
        self.assertIn('inodes_integrity_ok', results)
        self.assertIn('corrupted_files', results)
        self.assertEqual(results['inodes_checked'], 2)

class TestCrashSimulation(unittest.TestCase):
    
    def test_crash_simulation_basic(self):
        """Test básico de simulación de fallos"""
        disk = VirtualDisk(size_mb=1)
        fs = JournalingFileSystem(disk, journal_enabled=True)
        
        from src.crash_simulator import CrashSimulator
        crash_sim = CrashSimulator(disk, fs)
        
        # Verificar que se puede crear
        self.assertIsNotNone(crash_sim)
        
    def test_block_corruption(self):
        """Test de corrupción de bloques"""
        disk = VirtualDisk(size_mb=1)
        
        # Escribir en algunos bloques primero
        for i in range(5):
            disk.write_block(i, b"test data")
        
        # Corromper algunos bloques
        disk.mark_corrupted(2)
        disk.mark_corrupted(4)
        
        # Verificar estado
        self.assertEqual(disk.block_status[2].name, "CORRUPTED")
        self.assertEqual(disk.block_status[4].name, "CORRUPTED")
        self.assertEqual(disk.block_status[0].name, "USED")  # No corrupto

if __name__ == '__main__':
    unittest.main()