"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(_runtime_version.Domain.PUBLIC, 5, 29, 0, '', 'user.proto')
_sym_db = _symbol_database.Default()
from google.protobuf import empty_pb2 as google_dot_protobuf_dot_empty__pb2
from google.protobuf import timestamp_pb2 as google_dot_protobuf_dot_timestamp__pb2
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nuser.proto\x12\x04user\x1a\x1bgoogle/protobuf/empty.proto\x1a\x1fgoogle/protobuf/timestamp.proto"\xac\x01\n\x04User\x12\n\n\x02id\x18\x01 \x01(\t\x12\x12\n\nfirst_name\x18\x02 \x01(\t\x12\x11\n\tlast_name\x18\x03 \x01(\t\x12\r\n\x05phone\x18\x04 \x01(\t\x12\r\n\x05email\x18\x05 \x01(\t\x12\x12\n\navatar_url\x18\x06 \x01(\t\x12\x0f\n\x07role_id\x18\x07 \x01(\x05\x12.\n\ncreated_at\x18\x08 \x01(\x0b2\x1a.google.protobuf.Timestamp"-\n\x11CreateUserRequest\x12\x18\n\x04user\x18\x01 \x01(\x0b2\n.user.User"-\n\x11UpdateUserRequest\x12\x18\n\x04user\x18\x01 \x01(\x0b2\n.user.User"\x1c\n\x0eGetUserRequest\x12\n\n\x02id\x18\x01 \x01(\t"\x1f\n\x11DeleteUserRequest\x12\n\n\x02id\x18\x01 \x01(\t".\n\x11ListUsersResponse\x12\x19\n\x05users\x18\x01 \x03(\x0b2\n.user.User"/\n\x0bAvatarChunk\x12\x0f\n\x07user_id\x18\x01 \x01(\t\x12\x0f\n\x07content\x18\x02 \x01(\x0c2\xce\x02\n\x0bUserService\x121\n\nCreateUser\x12\x17.user.CreateUserRequest\x1a\n.user.User\x12+\n\x07GetUser\x12\x14.user.GetUserRequest\x1a\n.user.User\x121\n\nUpdateUser\x12\x17.user.UpdateUserRequest\x1a\n.user.User\x12=\n\nDeleteUser\x12\x17.user.DeleteUserRequest\x1a\x16.google.protobuf.Empty\x12<\n\tListUsers\x12\x16.google.protobuf.Empty\x1a\x17.user.ListUsersResponse\x12/\n\x0cUploadAvatar\x12\x11.user.AvatarChunk\x1a\n.user.User(\x01b\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'user_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_USER']._serialized_start = 83
    _globals['_USER']._serialized_end = 255
    _globals['_CREATEUSERREQUEST']._serialized_start = 257
    _globals['_CREATEUSERREQUEST']._serialized_end = 302
    _globals['_UPDATEUSERREQUEST']._serialized_start = 304
    _globals['_UPDATEUSERREQUEST']._serialized_end = 349
    _globals['_GETUSERREQUEST']._serialized_start = 351
    _globals['_GETUSERREQUEST']._serialized_end = 379
    _globals['_DELETEUSERREQUEST']._serialized_start = 381
    _globals['_DELETEUSERREQUEST']._serialized_end = 412
    _globals['_LISTUSERSRESPONSE']._serialized_start = 414
    _globals['_LISTUSERSRESPONSE']._serialized_end = 460
    _globals['_AVATARCHUNK']._serialized_start = 462
    _globals['_AVATARCHUNK']._serialized_end = 509
    _globals['_USERSERVICE']._serialized_start = 512
    _globals['_USERSERVICE']._serialized_end = 846