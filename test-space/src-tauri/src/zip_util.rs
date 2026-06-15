use std::io::Write;

pub fn create_zip_from_memory(files: &[super::ZipFileEntry], dest_path: &str) -> Result<String, String> {
    let file = std::fs::File::create(dest_path).map_err(|e| e.to_string())?;
    let mut zip = zip::ZipWriter::new(file);
    let options: zip::write::FileOptions<'_, ()> = zip::write::FileOptions::default()
        .compression_method(zip::CompressionMethod::Deflated);

    for entry in files {
        zip.start_file(&entry.filename, options.clone()).map_err(|e| e.to_string())?;
        zip.write_all(entry.content.as_bytes()).map_err(|e| e.to_string())?;
    }
    zip.finish().map_err(|e| e.to_string())?;
    Ok(dest_path.to_string())
}
