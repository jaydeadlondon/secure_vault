import binascii
from uuid import uuid4
from fastapi import UploadFile, HTTPException
from app.core.s3_client import s3_client
from app.models.file import FileMetadata
from app.services.crypto_utils import StreamEngine, generate_key, generate_nonce


async def upload_encrypted_file(file: UploadFile, user_id, db):
    key = generate_key()
    nonce = generate_nonce()
    file_uuid = uuid4()
    storage_path = str(file_uuid)

    encrypted_stream = EncryptedStream(file, key, nonce)

    async with s3_client.get_client() as s3:
        await s3.upload_fileobj(encrypted_stream, s3_client.bucket, storage_path)

    stored_key = binascii.hexlify(nonce).decode() + ":" + binascii.hexlify(key).decode()

    size = 0
    if file.size:
        size = file.size

    db_file = FileMetadata(
        id=file_uuid,
        user_id=user_id,
        original_filename=file.filename,
        storage_path=storage_path,
        size=size,
        content_type=file.content_type,
        encryption_key=stored_key,
    )
    db.add(db_file)
    await db.commit()
    await db.refresh(db_file)

    return db_file


async def download_decrypted_stream(file_id: str, user_id, db):
    db_file = await db.get(FileMetadata, file_id)
    if not db_file:
        raise HTTPException(404, "File not found")

    if db_file.user_id != user_id:
        raise HTTPException(403, "Not your file")

    nonce_hex, key_hex = db_file.encryption_key.split(":")
    nonce = binascii.unhexlify(nonce_hex)
    key = binascii.unhexlify(key_hex)

    engine = StreamEngine(key, nonce)
    decryptor = engine.decryptor()

    async def iter_file():
        async with s3_client.get_client() as s3:
            response = await s3.get_object(
                Bucket=s3_client.bucket, Key=db_file.storage_path
            )
            stream = response["Body"]
            async for chunk in stream.iter_chunks(chunk_size=65536):
                if chunk:
                    yield decryptor.update(chunk)
            yield decryptor.finalize()

    return iter_file, db_file.original_filename, db_file.content_type


async def delete_file_completely(file_id: str, user_id, db):
    db_file = await db.get(FileMetadata, file_id)
    if not db_file:
        raise HTTPException(404, "File not found")

    if db_file.user_id != user_id:
        raise HTTPException(403, "Not your file")

    async with s3_client.get_client() as s3:
        await s3.delete_object(Bucket=s3_client.bucket, Key=db_file.storage_path)

    await db.delete(db_file)
    await db.commit()
    return True


class EncryptedStream:
    def __init__(self, file: UploadFile, key: bytes, nonce: bytes):
        self.file = file
        self.engine = StreamEngine(key, nonce)
        self.encryptor = self.engine.encryptor()

    async def read(self, size: int = -1):
        chunk = await self.file.read(size)

        if not chunk:
            return b""

        encrypted_chunk = self.encryptor.update(chunk)
        return encrypted_chunk


async def get_all_files(db):
    from sqlalchemy import select

    stmt = select(FileMetadata).order_by(FileMetadata.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()