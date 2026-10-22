//! FFI Module - C-compatible interface for Python integration

use std::ffi::CString;
use std::os::raw::c_char;
use std::ptr;

/// Module initialization
pub fn register_ffi() {
    // This is called from the main lib.rs init
    // Individual functions are already marked with #[no_mangle]
}

/// Helper to convert Rust string to C string
pub fn to_c_string(s: String) -> *mut c_char {
    match CString::new(s) {
        Ok(c_str) => c_str.into_raw(),
        Err(_) => ptr::null_mut(),
    }
}

/// Helper to free C string (defined in lib.rs)
#[allow(clippy::not_unsafe_ptr_arg_deref)]
pub fn kde_theme_core_free_string(ptr: *mut c_char) {
    if !ptr.is_null() {
        unsafe {
            drop(CString::from_raw(ptr));
        }
    }
}

/// Get last error message (implementation in lib.rs)
pub fn kde_theme_core_get_error() -> *const c_char {
    ptr::null()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_to_c_string() {
        let s = "test".to_string();
        let c_str = to_c_string(s);
        assert!(!c_str.is_null());
        unsafe {
            drop(CString::from_raw(c_str));
        }
    }
}