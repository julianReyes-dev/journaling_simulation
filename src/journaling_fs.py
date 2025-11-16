import json
import time
from enum import Enum
from typing import List, Dict, Any
from dataclasses import dataclass
from .virtual_disk import VirtualDisk, Inode

class JournalEntryType(Enum):
    FILE_CREATE = "CREATE"
    FILE_WRITE = "WRITE"
    FILE_DELETE = "DELETE"
    METADATA_UPDATE = "METADATA"
    CHECKPOINT = "CHECKPOINT"

@dataclass
class JournalEntry:
    transaction_id: int
    entry_type: JournalEntryType
    timestamp: float
    data: Dict[str, Any]
    checksum: str

class JournalingFileSystem:
    """
    Implementa un sistema de archivos con journaling
    """
    
    def __init__(self, disk: VirtualDisk, journal_enabled: bool = True):
        self.disk = disk
        self.journal_enabled = journal_enabled
        self.journal: List[JournalEntry] = []
        self.current_transaction_id = 1
        self.checkpoint_interval = 5  # Operaciones entre checkpoints
        
    def begin_transaction(self) -> int:
        """Inicia una nueva transacción"""
        transaction_id = self.current_transaction_id
        self.current_transaction_id += 1
        return transaction_id
        
    def journal_operation(self, entry_type: JournalEntryType, operation_data: Dict[str, Any]):
        """Registra una operación en el journal"""
        if not self.journal_enabled:
            return
            
        entry = JournalEntry(
            transaction_id=self.current_transaction_id,
            entry_type=entry_type,
            timestamp=time.time(),
            data=operation_data,
            checksum=self._calculate_journal_checksum(operation_data)
        )
        self.journal.append(entry)
        
        # Crear checkpoint periódicamente
        if len(self.journal) % self.checkpoint_interval == 0:
            self._create_checkpoint()
    
    def create_file(self, filename: str, data: bytes) -> bool:
        """Crea un archivo con journaling"""
        transaction_id = self.begin_transaction()
        
        try:
            # Fase 1: Journaling - Registrar la operación
            if self.journal_enabled:
                self.journal_operation(JournalEntryType.FILE_CREATE, {
                    "filename": filename,
                    "size": len(data),
                    "data_checksum": self.disk.calculate_checksum(data),
                    "transaction_id": transaction_id
                })
            
            # Fase 2: Ejecución - Realizar la operación real
            blocks_needed = (len(data) + self.disk.block_size - 1) // self.disk.block_size
            free_blocks = self.disk.get_free_blocks(blocks_needed)
            
            if not free_blocks:
                raise Exception("No hay bloques libres suficientes")
                
            # Escribir datos en bloques
            for i, block_num in enumerate(free_blocks):
                start = i * self.disk.block_size
                end = start + self.disk.block_size
                block_data = data[start:end]
                self.disk.write_block(block_num, block_data)
            
            # Crear inodo
            inode = Inode(
                id=self.disk.next_inode_id,
                size=len(data),
                blocks=free_blocks,
                checksum=self.disk.calculate_checksum(data),
                created=time.time(),
                modified=time.time()
            )
            self.disk.inodes[inode.id] = inode
            self.disk.next_inode_id += 1
            
            # Registrar metadata en journal
            if self.journal_enabled:
                self.journal_operation(JournalEntryType.METADATA_UPDATE, {
                    "inode_id": inode.id,
                    "filename": filename,
                    "blocks": free_blocks,
                    "transaction_id": transaction_id
                })
            
            print(f" Archivo '{filename}' creado exitosamente (inodo: {inode.id})")
            return True
            
        except Exception as e:
            print(f" Error creando archivo '{filename}': {e}")
            return False
    
    def read_file(self, inode_id: int) -> Optional[bytes]:
        """Lee un archivo verificando integridad"""
        if inode_id not in self.disk.inodes:
            print(f" Inodo {inode_id} no encontrado")
            return None
            
        inode = self.disk.inodes[inode_id]
        data_blocks = []
        
        for block_num in inode.blocks:
            block_data = self.disk.read_block(block_num)
            if block_data:
                data_blocks.append(block_data)
            else:
                print(f"  Bloque {block_num} corrupto o no accesible")
                return None
                
        file_data = b''.join(data_blocks)[:inode.size]
        
        # Verificar integridad
        current_checksum = self.disk.calculate_checksum(file_data)
        if current_checksum != inode.checksum:
            print(f"  Checksum no coincide para inodo {inode_id}")
            print(f"   Esperado: {inode.checksum[:16]}...")
            print(f"   Obtenido: {current_checksum[:16]}...")
            
        return file_data
    
    def recover_from_journal(self) -> Dict[str, Any]:
        """
        Recupera el estado del sistema de archivos usando el journal
        después de un fallo
        """
        if not self.journal_enabled:
            return {"recovered": 0, "errors": 0, "pending_operations": []}
            
        recovery_stats = {"recovered": 0, "errors": 0, "pending_operations": []}
        
        print("Iniciando recuperación desde journal...")
        
        # Buscar operaciones pendientes (sin metadata confirmada)
        for entry in self.journal:
            if entry.entry_type == JournalEntryType.FILE_CREATE:
                filename = entry.data["filename"]
                data_checksum = entry.data["data_checksum"]
                
                # Verificar si existe un inodo con este checksum
                file_exists = False
                for inode in self.disk.inodes.values():
                    if inode.checksum == data_checksum:
                        file_exists = True
                        break
                
                if not file_exists:
                    recovery_stats["pending_operations"].append({
                        "type": "FILE_CREATE_PENDING",
                        "filename": filename,
                        "transaction_id": entry.transaction_id
                    })
                    recovery_stats["errors"] += 1
                    print(f"Operación pendiente: Crear archivo '{filename}'")
        
        recovery_stats["recovered"] = len(self.journal) - recovery_stats["errors"]
        print(f"Recuperación completada: {recovery_stats['recovered']} operaciones verificadas")
        
        return recovery_stats
    
    def _create_checkpoint(self):
        """Crea un punto de control en el journal"""
        checkpoint_data = {
            "timestamp": time.time(),
            "active_inodes": list(self.disk.inodes.keys()),
            "total_operations": len(self.journal),
            "transaction_id": self.current_transaction_id
        }
        
        checkpoint_entry = JournalEntry(
            transaction_id=self.current_transaction_id,
            entry_type=JournalEntryType.CHECKPOINT,
            timestamp=time.time(),
            data=checkpoint_data,
            checksum=self._calculate_journal_checksum(checkpoint_data)
        )
        self.journal.append(checkpoint_entry)
        print(f"Checkpoint creado (transacción {self.current_transaction_id})")
    
    def _calculate_journal_checksum(self, data: Dict[str, Any]) -> str:
        """Calcula checksum para entradas del journal"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def get_journal_stats(self) -> Dict[str, Any]:
        """Estadísticas del journal"""
        entry_types = {}
        for entry in self.journal:
            entry_type = entry.entry_type.value
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
            
        return {
            "total_entries": len(self.journal),
            "entry_types": entry_types,
            "journal_enabled": self.journal_enabled,
            "current_transaction": self.current_transaction_id
        }
        
    def list_files(self) -> List[Dict[str, Any]]:
        """Lista todos los archivos en el sistema"""
        files = []
        for inode_id, inode in self.disk.inodes.items():
            files.append({
                "inode_id": inode_id,
                "size": inode.size,
                "blocks": len(inode.blocks),
                "checksum": inode.checksum[:16] + "...",
                "created": time.strftime("%H:%M:%S", time.localtime(inode.created))
            })
        return files