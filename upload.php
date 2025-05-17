<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['video'])) {
    $uploadDir = __DIR__ . '/uploads/';
    $processedDir = __DIR__ . '/processed/';
    $uploadedFile = $_FILES['video']['tmp_name'];
    $filename = basename($_FILES['video']['name']);
    $targetFile = $uploadDir . $filename;
    $outputFile = $processedDir . 'processed_' . $filename;

    echo "<strong>Uploaded file path:</strong> $uploadedFile<br>";
    echo "<strong>Target path:</strong> $targetFile<br>";

    // Check for errors
    if ($_FILES['video']['error'] !== UPLOAD_ERR_OK) {
        echo "❌ Upload error: " . $_FILES['video']['error'];
        exit;
    }

    // Ensure upload directory exists
    if (!is_dir($uploadDir)) {
        echo "❌ Upload directory not found.";
        exit;
    }

    // Move uploaded file
    if (move_uploaded_file($uploadedFile, $targetFile)) {
        echo "✅ File uploaded to: $targetFile<br>";

        // Run Python script
        $escapedInput = escapeshellarg($targetFile);
        $escapedOutput = escapeshellarg($outputFile);
        $command = "python3 process_video.py $escapedInput $escapedOutput 2>&1";
        exec($command, $output, $returnCode);

        echo "<pre>";
        foreach ($output as $line) {
            echo htmlspecialchars($line) . "\n";
        }
        echo "</pre>";

        if ($returnCode === 0) {
            echo "<br>✅ Video processed successfully.<br>";
            echo "<a href='processed/processed_$filename' download>Download Processed Video</a>";
        } else {
            echo "<br>❌ Video processing failed.";
        }
    } else {
        echo "❌ Error saving uploaded file. Check folder permissions.";
    }
} else {
    echo "❌ No video uploaded.";
}
?>
